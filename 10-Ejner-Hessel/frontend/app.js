// Min Hessel – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { customerId: null, overview: null, workshops: [], repairSteps: [], booking: {} };

const REPAIR_TEXT = {
  MODTAGET: "Bilen er modtaget", DIAGNOSE: "Fejlfinding i gang", VENTER_PÅ_DELE: "Venter på reservedele",
  I_GANG: "Reparation i gang", KLAR_TIL_AFHENTNING: "Klar til afhentning", AFHENTET: "Afhentet",
};
const BOOKING_BADGE = { BEKRÆFTET: "ok", AFLYST: "muted", GENNEMFØRT: "" };
const SERVICE_TYPES = ["Serviceeftersyn", "Årligt eftersyn", "Hjulskift", "Fejlfinding", "Syn"];
const MONTHS = ["jan.", "feb.", "mar.", "apr.", "maj", "jun.", "jul.", "aug.", "sep.", "okt.", "nov.", "dec."];

function goTo(tab) {
  document.querySelector(`.tabs [data-tab="${tab}"]`).click();
}

// Datoer vises ensartet som 12.10.2026
function day(value) {
  if (!value) return "–";
  const [y, m, d] = value.slice(0, 10).split("-");
  return `${d}.${m}.${y}`;
}

function dayTime(value) {
  return value ? `${day(value)} kl. ${value.slice(11, 16)}` : "–";
}

function km(value) {
  return value === null || value === undefined ? "–" : `${Number(value).toLocaleString("da-DK")} km`;
}

function carName(car) {
  return `${car.brand} ${car.model}`;
}

function info(label, value) {
  return h("div", { class: "kpi" }, h("div", { class: "label" }, label), h("div", {}, h("strong", {}, value ?? "–")));
}

// ---------------------------------------------------------------- Billede af bilen: rigtigt foto eller en illustration af karrosseriet
const BODY = {
  LILLE: { belt: 60, roof: 30, rear: 34, roofFront: 136, wind: 166 },
  HATCHBACK: { belt: 58, roof: 30, rear: 26, roofFront: 150, wind: 180 },
  SEDAN: { belt: 58, roof: 32, rear: 62, roofFront: 150, wind: 182, trunk: true },
  STATIONCAR: { belt: 58, roof: 30, rear: 20, roofFront: 152, wind: 184 },
  SUV: { belt: 54, roof: 22, rear: 22, roofFront: 150, wind: 178, high: true },
  MPV: { belt: 56, roof: 22, rear: 20, roofFront: 140, wind: 174 },
  VAREVOGN: { belt: 56, roof: 12, rear: 16, roofFront: 160, wind: 192, cabOnly: true },     // ruder kun ved førerhuset
};

function carImage(car) {
  if (car.image_url) return h("div", { class: "car-img" }, h("img", { src: car.image_url, alt: carName(car) }));
  const b = BODY[car.body_type] ?? BODY.HATCHBACK;
  const bottom = b.high ? 80 : 84;
  const rear = b.trunk ? `L18,${b.belt} L50,${b.belt - 2} L${b.rear},${b.roof}` : `L18,${b.belt} L${b.rear},${b.roof}`;
  const body = `M18,${bottom} ${rear} L${b.roofFront},${b.roof} L${b.wind},${b.belt} L214,${b.belt + 4} Q222,${b.belt + 6} 222,70 L222,${bottom} Z`;
  const glassStart = b.cabOnly ? b.roofFront - 36 : b.rear + 10;
  const glass = `M${glassStart - 2},${b.belt - 3} L${glassStart},${b.roof + 5} L${b.roofFront - 2},${b.roof + 5} L${b.wind - 8},${b.belt - 3} Z`;
  const pillar = b.cabOnly ? "" : `<line x1="${(b.rear + b.roofFront) / 2 + 10}" y1="${b.roof + 5}" x2="${(b.rear + b.roofFront) / 2 + 14}" y2="${b.belt - 3}" stroke="rgba(0,0,0,0.25)" stroke-width="2"/>`;
  const color = /^#[0-9a-f]{3,6}$/i.test(car.color) ? car.color : "#9aa5ad";
  const svg = `<svg viewBox="0 0 240 110" xmlns="http://www.w3.org/2000/svg" role="img">
    <ellipse cx="120" cy="98" rx="104" ry="5" fill="rgba(0,0,0,0.12)"/>
    <path d="${body}" fill="${color}" stroke="rgba(0,0,0,0.35)" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="${glass}" fill="#cfe3f1" stroke="rgba(0,0,0,0.25)"/>
    ${pillar}
    <rect x="212" y="${b.belt + 8}" width="8" height="5" rx="2" fill="#ffe9a3"/>
    ${[60, 182].map((x) => `<circle cx="${x}" cy="${bottom}" r="15" fill="#22272b"/><circle cx="${x}" cy="${bottom}" r="7" fill="#b9c1c8"/>`).join("")}
  </svg>`;
  const box = h("div", { class: "car-img" });
  box.innerHTML = svg;                // kun egne tal og en valideret farve – ingen tekst fra databasen
  box.querySelector("svg").setAttribute("aria-label", carName(car));
  return box;
}

// ---------------------------------------------------------------- Kunde eller medarbejder (separate visninger)
async function start() {
  const [customers, workshops, repairSteps] = await Promise.all([api("/customers"), api("/workshops"), api("/repair-steps")]);
  Object.assign(state, { workshops, repairSteps });
  fillSelect($("#view-select"), [...customers.map((c) => ({ id: c.id, name: c.name })), { id: "staff", name: "Medarbejder (værksted)" }],
    (c) => c.name);
  await switchView($("#view-select").value);
}

async function switchView(value) {
  const staff = value === "staff";
  $("#customer-tabs").hidden = staff;
  $("#staff-tabs").hidden = !staff;
  if (staff) {
    goTo("workshop");
    loadWorkshop();
  } else {
    state.customerId = Number(value);
    await loadAll();
    goTo("cars");
  }
}

$("#view-select").addEventListener("change", (event) => switchView(event.target.value));

async function loadAll() {
  state.overview = await api(`/customers/${state.customerId}/overview`);
  renderCars();
  startBooking();
  renderBookings();
  renderDocuments();
  loadRepairs();
  loadClimateCars();
}

// ---------------------------------------------------------------- Mine biler
function renderCars() {
  const { cars, notifications } = state.overview;
  $("#notifications").replaceChildren(...notifications.map((n) => h("div", { class: "card highlight" }, "🔔 ", n)));
  $("#car-cards").replaceChildren(...cars.map((car) => h("div", { class: "card car-card" },
    carImage(car),
    h("div", { class: "brand" }, car.brand),
    h("h2", { style: "margin:0" }, car.model),
    h("div", { class: "facts" },
      h("span", {}, car.registration), h("span", {}, car.year), h("span", {}, car.fuel), h("span", {}, car.gearbox),
      h("span", {}, km(car.mileage_km)), h("span", {}, car.ownership)),
    car.active_repair ? h("p", {}, "🔧 ", h("strong", {}, REPAIR_TEXT[car.active_repair.status]), " ",
      h("a", { href: "#", onclick: (e) => { e.preventDefault(); goTo("repairs"); } }, "Se status")) : null,
    h("p", { style: "margin:0" }, "Næste booking: ", car.next_booking
      ? h("strong", {}, `${day(car.next_booking.date)} kl. ${car.next_booking.time}`)
      : h("span", { class: "muted" }, "ingen")),
    h("p", { style: "margin:0" }, "Næste service: ", day(car.next_service_date), " ", car.service_due_soon ? badge("snart", "warn") : null),
    h("p", { style: "margin:0" }, "Næste syn: ", day(car.next_inspection_date), " ", car.inspection_due_soon ? badge("snart", "warn") : null),
    h("div", { class: "actions" },
      h("button", { onclick: () => showCar(car.id) }, "Biloplysninger"),
      h("button", { class: "secondary", onclick: () => startBooking(car.id) }, "Book værksted")))));
}

function repairProgress(repair) {
  return h("div", { class: "progress" }, Array.from({ length: repair.steps }, (_, i) => h("span", { class: i < repair.step ? "done" : "" })));
}

// ---------------------------------------------------------------- Biloplysninger
async function showCar(carId) {
  const d = await api(`/cars/${carId}/details`);
  const c = d.car;
  const electric = c.battery_kwh !== null;
  $("#car-details").replaceChildren(
    h("div", { class: "card highlight" },
      h("div", { class: "grid wide" },
        carImage(c),
        h("div", {},
          h("div", { class: "brand" }, c.brand),
          h("h2", {}, `${c.model}`),
          h("p", {}, h("strong", {}, c.registration), ` · stelnr. ${c.vin ?? "–"}`),
          h("button", { onclick: () => startBooking(c.id) }, "Book værksted"))),
      h("h3", {}, "Bilen"),
      h("div", { class: "kpis" },
        info("Årgang", c.year), info("Drivmiddel", c.fuel), info("Gearkasse", c.gearbox), info("Kilometer", km(c.mileage_km)),
        electric ? info("Batterikapacitet", `${c.battery_kwh.toLocaleString("da-DK")} kWh`) : null,
        electric ? info("Rækkevidde (el)", km(c.range_km)) : null),
      h("h3", {}, "Service, syn og garanti"),
      h("div", { class: "kpis" },
        info("Næste service", day(c.next_service_date)), info("Næste syn", day(c.next_inspection_date)),
        info("Garanti til", h("span", {}, day(c.warranty_until), " ", c.warranty_active ? badge("aktiv", "ok") : badge("udløbet", "muted")))),
      c.ownership === "Leaset" ? h("div", {},
        h("h3", {}, "Leasing"),
        h("div", { class: "kpis" },
          info("Leasingselskab", c.leasing_company), info("Udløber", day(c.leasing_end)),
          info("Måneder tilbage", c.leasing_months_left), info("Km pr. år", km(c.leasing_km_per_year)),
          info("Ydelse pr. måned", formatKr(c.leasing_monthly)))) : null),
    h("div", { class: "grid wide" },
      h("div", { class: "card" }, h("h3", {}, "Servicehistorik"), h("div", { id: "service-table" })),
      h("div", { class: "card" }, h("h3", {}, "Dokumenter for bilen"), h("div", { id: "car-doc-table" }))),
  );
  renderTable($("#service-table"), d.service_history, [
    { label: "Dato", class: "nowrap", render: (s) => day(s.date) },
    { label: "Type", key: "type" },
    { label: "Værksted", class: "nowrap", key: "workshop_name" },
    { label: "Km", class: "num nowrap", render: (s) => km(s.mileage_km) },
    { label: "Pris", class: "num nowrap", render: (s) => formatKr(s.price) },
    { label: "Udført", key: "description" },
  ], "Ingen service registreret");
  renderTable($("#car-doc-table"), d.documents, [
    { label: "Dato", class: "nowrap", render: (x) => day(x.date) },
    { label: "Titel", key: "title" },
    { label: "", render: (x) => documentButtons(x) },
  ], "Ingen dokumenter");
  goTo("car");
}

// ---------------------------------------------------------------- Booking i tydelige trin med oversigt før bekræftelse
function startBooking(carId) {
  state.booking = { car_id: carId ?? null, service_type: SERVICE_TYPES[0] };
  $("#booking-title").textContent = "Book tid på værksted";
  renderBookingStep(carId ? 2 : 1);
  if (carId) goTo("bookings");
}

function setStep(n) {
  document.querySelectorAll("#booking-steps span").forEach((s, i) => {
    s.className = i + 1 === n ? "active" : i + 1 < n ? "done" : "";
  });
}

function nextDays(count) {
  const days = [];
  const d = new Date();
  while (days.length < count) {
    d.setDate(d.getDate() + 1);
    if (d.getDay() !== 0 && d.getDay() !== 6) {
      days.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`);
    }
  }
  return days;
}

async function renderBookingStep(step) {
  const b = state.booking;
  const car = state.overview.cars.find((c) => c.id === b.car_id);
  const workshop = state.workshops.find((w) => w.id === b.workshop_id);
  setStep(step);
  const back = (n) => h("button", { type: "button", class: "secondary", onclick: () => renderBookingStep(n) }, "Tilbage");
  const choice = (selected, onclick, ...content) => h("button", { type: "button", class: `choice ${selected ? "selected" : ""}`, onclick }, ...content);
  let content;
  if (step === 1) {
    content = [h("p", {}, "Vælg den bil, der skal på værksted:"),
      h("div", { class: "choices" }, state.overview.cars.map((c) => choice(c.id === b.car_id, () => { b.car_id = c.id; renderBookingStep(2); },
        h("strong", {}, carName(c)), h("span", { class: "muted" }, c.registration))))];
  } else if (step === 2) {
    const fits = state.workshops.filter((w) => w.brands.split(",").includes(car.brand));
    content = [h("p", {}, `Værksteder der servicerer ${car.brand}:`),
      h("div", { class: "choices" }, fits.map((w) => choice(w.id === b.workshop_id, () => { b.workshop_id = w.id; renderBookingStep(3); },
        h("strong", {}, w.name), h("span", { class: "muted" }, w.address)))),
      h("div", { class: "actions", style: "margin-top:12px" }, back(1))];
  } else if (step === 3) {
    const typeSelect = h("select", { onchange: (e) => { b.service_type = e.target.value; } }, SERVICE_TYPES.map((t) => h("option", {}, t)));
    typeSelect.value = b.service_type;
    content = [h("label", {}, "Hvad skal laves?", typeSelect),
      h("p", {}, "Vælg dato (hverdage):"),
      h("div", { class: "choices" }, nextDays(10).map((d) => {
        const date = new Date(d);
        return choice(d === b.date, () => { b.date = d; b.time = null; renderBookingStep(4); },
          h("strong", {}, `${["søn", "man", "tir", "ons", "tor", "fre", "lør"][date.getDay()]}dag ${day(d)}`));
      })),
      h("div", { class: "actions", style: "margin-top:12px" }, back(2))];
  } else if (step === 4) {
    const slots = await api(`/available-times?workshop_id=${b.workshop_id}&date=${b.date}`);
    content = [h("p", {}, `Ledige tider ${day(b.date)} på ${workshop.name}:`),
      h("div", { class: "slots" }, slots.map((s) => h("button", {
        type: "button", class: s.time === b.time ? "" : "secondary", disabled: !s.available,
        onclick: () => { b.time = s.time; renderBookingStep(5); },
      }, s.time))),
      h("div", { class: "actions", style: "margin-top:12px" }, back(3))];
  } else {
    const notes = h("textarea", { placeholder: "Besked til værkstedet (valgfri)", oninput: (e) => { b.notes = e.target.value; } }, b.notes ?? "");
    content = [h("h3", {}, "Oversigt – tjek dine valg"),
      h("dl", { class: "summary" },
        h("dt", {}, "Bil"), h("dd", {}, `${carName(car)} (${car.registration})`),
        h("dt", {}, "Værksted"), h("dd", {}, `${workshop.name}, ${workshop.address}`),
        h("dt", {}, "Type"), h("dd", {}, b.service_type),
        h("dt", {}, "Tidspunkt"), h("dd", {}, `${day(b.date)} kl. ${b.time}`)),
      h("label", {}, "Besked til værkstedet", notes),
      h("div", { class: "actions" }, back(4), h("button", { onclick: confirmBooking }, b.id ? "Gem ændring" : "Bekræft booking"))];
  }
  $("#booking-step").replaceChildren(...content);
}

async function confirmBooking() {
  const { id, ...body } = state.booking;
  await run(() => api(id ? `/bookings/${id}` : "/bookings", { method: id ? "PUT" : "POST", body }),
    id ? "Bookingen er ændret" : "Bookingen er bekræftet");
  await loadAll();
}

function renderBookings() {
  renderTable($("#booking-table"), state.overview.bookings, [
    { label: "Dato", class: "nowrap", render: (b) => `${day(b.date)} kl. ${b.time}` },
    { label: "Bil", class: "nowrap", render: (b) => `${b.brand} ${b.model}` },
    { label: "Værksted", class: "nowrap", key: "workshop_name" },
    { label: "Type", key: "service_type" },
    { label: "Status", render: (b) => badge(b.status, BOOKING_BADGE[b.status]) },
    {
      label: "",
      render: (b) => (b.status !== "BEKRÆFTET" ? "" : h("div", { class: "actions" },
        h("button", { class: "small secondary", onclick: () => editBooking(b) }, "Ret"),
        h("button", { class: "small secondary", onclick: () => cancelBooking(b) }, "Aflys"))),
    },
  ], "Ingen bookinger");
}

function editBooking(booking) {
  state.booking = { id: booking.id, car_id: booking.car_id, workshop_id: booking.workshop_id, service_type: booking.service_type, date: booking.date, time: booking.time, notes: booking.notes };
  $("#booking-title").textContent = `Ret booking #${booking.id}`;
  renderBookingStep(5);
  $("#booking-title").scrollIntoView({ behavior: "smooth" });
}

async function cancelBooking(booking) {
  if (!confirm("Aflys bookingen?")) return;
  await run(() => api(`/bookings/${booking.id}`, { method: "PUT", body: { status: "AFLYST" } }), "Bookingen er aflyst");
  loadAll();
}

// ---------------------------------------------------------------- Reparationsstatus
async function loadRepairs() {
  const repairs = await api(`/customers/${state.customerId}/repairs`);
  $("#repair-list").replaceChildren(...(repairs.length ? repairs.map((r) => h("div", { class: "card" },
    h("div", { class: "grid wide" },
      h("div", {},
        h("div", { class: "brand" }, r.brand),
        h("h2", {}, `${r.model} · ${r.registration}`),
        h("p", {}, r.description),
        h("p", { style: "font-size:1.15rem" }, "🔧 ", h("strong", {}, r.status_text)),
        repairProgress(r),
        h("div", { class: "kpis" },
          info("Forventet færdig", day(r.estimated_ready)),
          info("Værksted", r.workshop_name ?? "–"),
          info("Sidst opdateret", dayTime(r.updated_at)))),
      h("div", {},
        h("h3", {}, "Beskeder fra værkstedet"),
        h("ul", { class: "timeline" }, r.updates.map((u) => h("li", {},
          h("small", { class: "muted" }, dayTime(u.created_at)), " ", badge(REPAIR_TEXT[u.status], u.status === "KLAR_TIL_AFHENTNING" ? "ok" : ""),
          u.message ? h("div", {}, u.message) : null))))))) : [h("div", { class: "card" }, h("p", { class: "empty" }, "Ingen af dine biler er på værksted lige nu."))]));
}

// ---------------------------------------------------------------- Aftaler og dokumenter: søg, filtrér, åbn og download
function documentButtons(doc) {
  const url = `${API_BASE}/api/documents/${doc.id}/file`;
  return h("div", { class: "actions" },
    h("a", { class: "btn", href: url, target: "_blank", rel: "noopener" }, "📄 Åbn"),
    h("a", { class: "btn secondary", href: `${url}?download=1` }, "⬇ Download"));
}

function renderDocuments() {
  const form = $("#doc-filter");
  const cars = state.overview.cars;
  if (form.dataset.customer !== String(state.customerId)) {
    fillSelect(form.elements.car_id, [...cars, { id: "general", brand: "Generelt", model: "(alle biler)" }], carName, { placeholder: "Alle biler" });
    form.dataset.customer = state.customerId;
  }
  const { q = "", car_id: carId = "", category = "" } = formToJson(form);
  const names = Object.fromEntries(cars.map((c) => [c.id, carName(c)]));
  const docs = state.overview.documents.filter((d) => (!category || d.category === category)
    && (!carId || (carId === "general" ? !d.car_id : d.car_id === Number(carId)))
    && (!q || `${d.title} ${d.description ?? ""} ${names[d.car_id] ?? ""}`.toLowerCase().includes(q.toLowerCase())));
  renderTable($("#document-table"), docs, [
    { label: "Dato", class: "nowrap", render: (d) => day(d.date) },
    { label: "Titel", key: "title" },
    { label: "Kategori", render: (d) => badge(d.category) },
    { label: "Bil", class: "nowrap", render: (d) => names[d.car_id] ?? "Generelt" },
    { label: "Beskrivelse", key: "description" },
    { label: "", render: (d) => documentButtons(d) },
  ], "Ingen dokumenter matcher søgningen");
}

$("#doc-filter").addEventListener("input", renderDocuments);
$("#doc-filter").addEventListener("submit", (event) => event.preventDefault());

// ---------------------------------------------------------------- Forbrug og klima
function loadClimateCars() {
  const select = $("#climate-car");
  fillSelect(select, state.overview.cars, (c) => `${carName(c)} (${c.registration})`);
  loadClimate();
}

async function loadClimate() {
  const carId = $("#climate-car").value;
  if (!carId) return;
  renderClimate(await api(`/cars/${carId}/consumption`));
}

function renderClimate(k) {
  const unit = k.unit_per_100;
  const max = Math.max(...k.logs.map((l) => l.per_100), k.goal?.target_per_100 ?? 0) * 1.15;
  const goalForm = h("form", { class: "toolbar" },
    h("label", {}, `Mit mål (${unit})`, h("input", { type: "number", name: "target_per_100", step: "0.1", min: "0.1", required: true, value: k.goal?.target_per_100 ?? "" })),
    h("button", {}, "Gem mål"));
  goalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    renderClimate(await run(() => api(`/cars/${k.car.id}/goal`, { method: "PUT", body: formToJson(goalForm) }), "Målet er gemt"));
  });
  const logForm = h("form", { class: "toolbar" },
    h("label", {}, "Måned", h("input", { type: "month", name: "month", required: true, value: new Date().toISOString().slice(0, 7) })),
    h("label", {}, "Kørt (km)", h("input", { type: "number", name: "km", min: 1, required: true })),
    h("label", {}, `Forbrug (${k.unit})`, h("input", { type: "number", name: "amount", step: "0.1", min: "0.1", required: true })),
    h("button", {}, "Registrér"));
  logForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    renderClimate(await run(() => api(`/cars/${k.car.id}/consumption`, { method: "POST", body: formToJson(logForm) }), "Forbruget er registreret"));
  });
  const s = k.savings;
  $("#climate").replaceChildren(
    h("div", { class: "kpis" },
      info("Forbrug nu (3 mdr.)", k.current_per_100 ? `${k.current_per_100.toLocaleString("da-DK")} ${unit}` : "–"),
      info("Km pr. år", km(k.yearly_km)),
      info("Udgift pr. år", formatKr(k.yearly_cost)),
      info("CO₂ pr. år", k.yearly_co2_kg !== null ? `${k.yearly_co2_kg.toLocaleString("da-DK")} kg` : "–")),
    h("div", { class: "grid wide" },
      h("div", { class: "card" },
        h("h3", {}, `Forbrug pr. måned (${unit})`),
        h("div", { class: "bars" },
          k.goal ? h("div", { class: "goal-line", style: `bottom:${(k.goal.target_per_100 / max) * 150 + 18}px`, title: "Mål" }) : null,
          k.logs.map((l) => h("div", { class: "b", title: `${l.km} km · ${l.amount} ${k.unit} · ${formatKr(l.cost)} · ${l.co2_kg} kg CO₂` },
            h("small", {}, l.per_100.toLocaleString("da-DK")),
            h("span", { style: `height:${(l.per_100 / max) * 150}px` }),
            h("small", {}, `${MONTHS[Number(l.month.slice(5)) - 1]} ${l.month.slice(2, 4)}`)))),
        k.goal ? h("p", { class: "muted" }, "Stiplet linje = dit mål") : null,
        h("h3", {}, "Registrér en måned"), logForm),
      h("div", { class: "card" },
        h("h3", {}, "Sæt et mål og se besparelsen"), goalForm,
        s ? (s.reached
          ? h("div", { class: "saving" }, h("div", { class: "value" }, "🎉 Målet er nået"), h("p", {}, "Dit forbrug de seneste 3 måneder er på eller under målet."))
          : h("div", { class: "saving" },
            h("p", { style: "margin:0" }, `Når du når ${s.target_per_100.toLocaleString("da-DK")} ${unit}, sparer du ca.:`),
            h("div", { class: "value" }, `${formatKr(s.kr_per_year)} om året`),
            h("div", { class: "value" }, `${s.co2_kg_per_year.toLocaleString("da-DK")} kg CO₂ om året`),
            h("small", { class: "muted" }, `${s.units_per_year.toLocaleString("da-DK")} ${k.unit} mindre ved ${km(k.yearly_km)} om året. Pris ${formatKr(k.price_per_unit)} pr. ${k.unit} og ${k.co2_kg_per_unit} kg CO₂ pr. ${k.unit} (antagelser).`)))
          : h("p", { class: "muted" }, "Sæt et mål for at se, hvad et lavere forbrug kan spare i kroner og CO₂."),
        h("h3", {}, "Gode råd"),
        h("ul", {}, k.tips.map((t) => h("li", {}, t))))));
}

$("#climate-car").addEventListener("change", loadClimate);

// ---------------------------------------------------------------- Værksted (medarbejder)
async function loadWorkshop() {
  const [repairs, cars] = await Promise.all([api("/repairs"), api("/cars")]);
  const names = Object.fromEntries(cars.map((c) => [c.id, `${carName(c)} (${c.registration})`]));
  renderTable($("#repair-admin"), repairs.filter((r) => r.status !== "AFHENTET"), [
    { label: "Bil", class: "nowrap", render: (r) => names[r.car_id] },
    { label: "Reparation", key: "description" },
    { label: "Opdatér", render: (r) => repairUpdateForm(r) },
    { label: "Opdateret", class: "nowrap", render: (r) => dayTime(r.updated_at) },
  ], "Ingen igangværende reparationer");
  for (const form of [$("#repair-form"), $("#service-form")]) {
    fillSelect(form.elements.car_id, cars, (c) => names[c.id]);
    fillSelect(form.elements.workshop_id, state.workshops, (w) => w.name);
  }
}

function repairUpdateForm(r) {
  const form = h("form", { class: "toolbar" },
    h("select", { name: "status" }, state.repairSteps.map((s) => h("option", { value: s, selected: s === r.status }, REPAIR_TEXT[s]))),
    h("input", { type: "date", name: "estimated_ready", value: r.estimated_ready ?? "" }),
    h("input", { name: "message", placeholder: "Ny besked til kunden" }),
    h("button", { class: "small" }, "Gem"));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await run(() => api(`/repairs/${r.id}`, { method: "PUT", body: formToJson(form) }), "Reparationen er opdateret – kunden kan se det nu");
    loadWorkshop();
  });
  return form;
}

bindCrudForm($("#repair-form"), "repairs", loadWorkshop);
bindCrudForm($("#service-form"), "service-history", loadWorkshop);

// ---------------------------------------------------------------- Start
setupTabs((tab) => {
  if (tab === "repairs" && state.customerId) loadRepairs();
  if (tab === "climate" && state.customerId) loadClimate();
});
start().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
