// ---- Туры (каталог) ----
const tours = [
  {
    id: 1,
    country: "egypt",
    title: "Каир + Пирамиды Гизы (экскурсии)",
    days: 5,
    style: "excursions",
    priceKZT: 155000,
    hotel: "4★ городской отель",
    img: "https://images.unsplash.com/photo-1568322445389-f64ac2515020?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 2,
    country: "egypt",
    title: "Хургада (пляж + all inclusive)",
    days: 7,
    style: "beach",
    priceKZT: 175000,
    hotel: "4★ all inclusive",
    img: "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 3,
    country: "egypt",
    title: "Шарм-эль-Шейх (море + дайвинг)",
    days: 10,
    style: "beach",
    priceKZT: 235000,
    hotel: "5★ resort",
    img: "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 4,
    country: "dubai",
    title: "Дубай City Break (небоскрёбы + экскурсии)",
    days: 4,
    style: "excursions",
    priceKZT: 210000,
    hotel: "4★ Downtown",
    img: "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 5,
    country: "dubai",
    title: "Dubai Luxury (Burj area + премиум)",
    days: 5,
    style: "luxury",
    priceKZT: 320000,
    hotel: "5★ luxury",
    img: "https://images.unsplash.com/photo-1526495124232-a04e1849168c?auto=format&fit=crop&w=1200&q=80",
  },
  {
    id: 6,
    country: "dubai",
    title: "Дубай (шопинг + развлечения)",
    days: 7,
    style: "shopping",
    priceKZT: 260000,
    hotel: "4★ near mall",
    img: "https://images.unsplash.com/photo-1528702748617-c64d49f918af?auto=format&fit=crop&w=1200&q=80",
  },
];

const tourList = document.getElementById("tourList");
const chips = document.querySelectorAll(".chip");
const budgetInput = document.getElementById("budgetInput");
const styleSelect = document.getElementById("styleSelect");
const daysSelect = document.getElementById("daysSelect");
const recommendBtn = document.getElementById("recommendBtn");

let activeFilter = "all";

function countryLabel(country) {
  return country === "egypt" ? "Египет" : "Дубай";
}

function styleLabel(style) {
  const m = {
    any: "Любой",
    beach: "Пляж",
    excursions: "Экскурсии",
    luxury: "Люкс",
    shopping: "Шопинг",
    family: "Семейный",
  };
  return m[style] || style;
}

function formatKZT(n) {
  return `${String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ")} KZT`;
}

function renderTours(list) {
  tourList.innerHTML = "";

  if (!list.length) {
    tourList.innerHTML = `<div class="muted">Нет туров по выбранным параметрам 😅</div>`;
    return;
  }

  list.forEach((t) => {
    const card = document.createElement("div");
    card.className = "tour";
    card.innerHTML = `
      <img src="${t.img}" alt="${t.title}">
      <div class="tour-body">
        <div class="badges">
          <span class="badge">${countryLabel(t.country)}</span>
          <span class="badge">${t.days} дней</span>
          <span class="badge">${styleLabel(t.style)}</span>
        </div>

        <div class="tour-title">${t.title}</div>
        <div class="tour-meta">Отель: ${t.hotel}</div>

        <div class="tour-footer">
          <div class="price">от ${formatKZT(t.priceKZT)}</div>
          <button class="small-btn" data-tour="${t.id}">В AI-чат</button>
        </div>
      </div>
    `;
    tourList.appendChild(card);
  });

  document.querySelectorAll(".small-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = Number(btn.getAttribute("data-tour"));
      const tour = tours.find((x) => x.id === id);
      if (!tour) return;

      chatInput.value =
        `Хочу тур: "${tour.title}". ` +
        `Направление: ${countryLabel(tour.country)}, ${tour.days} дней, ` +
        `бюджет около ${formatKZT(tour.priceKZT)}, стиль: ${styleLabel(tour.style)}. ` +
        `Посоветуй что посмотреть и что взять с собой.`;
      document.getElementById("ai").scrollIntoView({ behavior: "smooth" });
      chatInput.focus();
    });
  });
}

function applyCountryFilter(filter) {
  activeFilter = filter;
  chips.forEach((c) => c.classList.toggle("is-active", c.dataset.filter === filter));
  const list = filter === "all" ? tours : tours.filter((t) => t.country === filter);
  renderTours(list);
}

chips.forEach((chip) => chip.addEventListener("click", () => applyCountryFilter(chip.dataset.filter)));

function recommend() {
  const budget = Number(budgetInput.value || 0);
  const style = styleSelect.value;
  const days = daysSelect.value === "any" ? null : Number(daysSelect.value);

  let list = [...tours];

  if (activeFilter !== "all") list = list.filter((t) => t.country === activeFilter);
  if (style !== "any") list = list.filter((t) => t.style === style);
  if (days) list = list.filter((t) => t.days === days);

  if (budget > 0) {
    list.sort((a, b) => Math.abs(a.priceKZT - budget) - Math.abs(b.priceKZT - budget));
    list = list.slice(0, 3);
  }

  renderTours(list);
}

recommendBtn.addEventListener("click", recommend);
applyCountryFilter("all");

// ---- AI Чат ----
const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");

function addMsg(text, who) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
  const text = (chatInput.value || "").trim();
  if (!text) return;

  addMsg(text, "user");
  chatInput.value = "";
  sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        context: {
          agency: "ISLAM TOUR",
          destinations: ["Египет", "Дубай"],
          currency: "KZT",
          tour_catalog: tours.map((t) => ({
            country: t.country,
            title: t.title,
            days: t.days,
            style: t.style,
            priceKZT: t.priceKZT,
          })),
        },
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || "Ошибка сервера");
    addMsg(data.reply, "bot");
  } catch (e) {
    addMsg("Ошибка: " + e.message, "bot");
  } finally {
    sendBtn.disabled = false;
  }
}

sendBtn.addEventListener("click", sendMessage);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

addMsg(
  "Привет! Я AI-консультант ISLAM TOUR 🙂\n" +
  "Напиши: Египет/Дубай, бюджет (KZT), дни/даты, сколько людей и стиль — я подберу варианты.",
  "bot"
);