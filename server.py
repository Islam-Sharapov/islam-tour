#!/usr/bin/env python3
import os
import json
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

SYSTEM_INSTRUCTIONS = """
Ты — AI-консультант туристического агентства ISLAM TOUR (учебный проект для Ислам Шарапов, АТУ).
Отвечай по-русски, дружелюбно и структурированно.

Правила:
- Уточняй: бюджет (KZT), длительность/даты, количество людей, стиль отдыха.
- Предлагай 2–3 варианта по Египту или Дубаю (если дан каталог — опирайся на него).
- Давай советы: погода, одежда, что посмотреть, документы/виза (без категоричности).
- Не выдумывай точные цены билетов/отелей — говори “ориентировочно”.
""".strip()


def load_env_if_exists():
    """
    Мини-лоадер .env без зависимостей.
    Подхватит переменные, если их нет в окружении.
    """
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass


def safe_json(handler: BaseHTTPRequestHandler, status: int, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def serve_file(handler: BaseHTTPRequestHandler, file_path: str):
    if not os.path.isfile(file_path):
        handler.send_response(404)
        handler.send_header("Content-Type", "text/plain; charset=utf-8")
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        handler.wfile.write(b"Not Found")
        return

    ctype, _ = mimetypes.guess_type(file_path)
    if not ctype:
        ctype = "application/octet-stream"

    with open(file_path, "rb") as f:
        data = f.read()

    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")  # меньше проблем с кешем
    handler.end_headers()
    handler.wfile.write(data)


def extract_text_from_responses_api(data: dict) -> str:
    """
    Надёжно вытаскивает текст из Responses API.
    Иногда output_text пустой, тогда текст лежит в output -> message -> content.
    """
    # 1) быстрый путь
    text = (data.get("output_text") or "").strip()
    if text:
        return text

    # 2) разбор output items
    out = data.get("output", [])
    chunks = []

    if isinstance(out, list):
        for item in out:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict):
                    continue
                # чаще всего текст здесь
                if c.get("type") in ("output_text", "text"):
                    t = (c.get("text") or "").strip()
                    if t:
                        chunks.append(t)

    joined = "\n".join(chunks).strip()
    if joined:
        return joined

    # 3) incomplete -> покажем причину
    if data.get("status") == "incomplete":
        details = data.get("incomplete_details") or {}
        return f"Ответ incomplete: {details}"

    return ""


def openai_chat(user_message: str, context: dict):
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "gpt-5-mini").strip()

    if not api_key:
        return (False, "OPENAI_API_KEY не задан. Создай .env и вставь ключ, либо выставь переменную окружения.")

    # Сжимаем контекст (каталог туров)
    ctx_text = ""
    try:
        catalog = context.get("tour_catalog", [])
        if isinstance(catalog, list) and catalog:
            lines = ["Каталог туров (ориентируйся на него при рекомендациях):"]
            for t in catalog[:20]:
                lines.append(
                    f"- {t.get('title')} | страна={t.get('country')} | дней={t.get('days')} | "
                    f"стиль={t.get('style')} | ценаKZT={t.get('priceKZT')}"
                )
            ctx_text = "\n".join(lines)
    except Exception:
        ctx_text = ""

    payload = {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": f"{ctx_text}\n\nСообщение клиента:\n{user_message}".strip()
    }

    req = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = extract_text_from_responses_api(data)

            if not text:
                # покажем минимум, чтобы понять, что вернул API
                return (False, f"Пусто. status={data.get('status')}, id={data.get('id')}")

            return (True, text)

    except HTTPError as e:
        try:
            err = e.read().decode("utf-8")
        except Exception:
            err = str(e)

        # Если квота закончилась — это частый кейс
        if "insufficient_quota" in err:
            return (False, "Квота API закончилась (insufficient_quota). Нужно подключить Billing/пополнить лимит в OpenAI Platform.")

        return (False, f"OpenAI HTTPError: {e.code} {e.reason}. {err}")

    except URLError as e:
        return (False, f"OpenAI URLError: {e}")

    except Exception as e:
        return (False, f"OpenAI Error: {e}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("", "/"):
            return serve_file(self, os.path.join(PUBLIC_DIR, "index.html"))

        if path == "/health":
            return safe_json(self, 200, {"status": "ok"})

        # статика из /public
        file_path = os.path.normpath(os.path.join(PUBLIC_DIR, path.lstrip("/")))
        if not file_path.startswith(PUBLIC_DIR):
            return safe_json(self, 403, {"error": "forbidden"})
        return serve_file(self, file_path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path != "/api/chat":
            return safe_json(self, 404, {"error": "not found"})

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            return safe_json(self, 400, {"error": "invalid json"})

        message = (data.get("message") or "").strip()
        context = data.get("context") or {}

        if not message:
            return safe_json(self, 400, {"error": "message is required"})

        ok, result = openai_chat(message, context)
        if ok:
            return safe_json(self, 200, {"reply": result})
        else:
            return safe_json(self, 500, {"error": result})


def main():
    load_env_if_exists()

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))

    print("== ISLAM TOUR Monolith ==")
    print(f"Serving on: http://{host}:{port}")
    if os.environ.get("OPENAI_API_KEY"):
        print(f"OpenAI model: {os.environ.get('OPENAI_MODEL','gpt-5-mini')}")
    else:
        print("WARNING: OPENAI_API_KEY not set (chat won't work)")

    httpd = HTTPServer((host, port), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()