// Min Hessel – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { customerId: null, overview: null, workshops: [], repairSteps: [] };

const REPAIR_TEXT = {
  MODTAGET: "Bilen er modtaget", DIAGNOSE: "Fejlfinding i gang", VENTER_PÅ_DELE: "Venter på reservedele",
  I_GANG: "Reparation i gang", KLAR_TIL_AFHENTNING: "Klar til afhentning", AFHENTET: "Afhentet",
};
const BOOKING_BADGE = { BEKRÆFTET: "ok", AFLYST: "muted", GENNEMFØRT: "" };

function goTo(tab) {
  document.querySelector(`.tabs [data-tab="${tab}"]`).click();
}

// ---------------------------------------------------------------- Indlæsning
async function loadAll() {
  state.overview = await api(`/customers/${state.customerId}/overview`);
  renderCars();
  renderBookings();
  renderDocuments();
  loadWorkshop();
}

// ---------------------------------------------------------------- Mine biler
function renderCars() {
  const { cars, notifications } = state.overview;
  $("#notifications").replaceChildren(...notifications.map((n) => h("div", { class: "card highlight" }, "🔔 ", n)));
  $("#car-cards").replaceChildren(...cars.map((car) => h("div", { class: "card" },
    h("div", { class: "brand" }, car.brand),
    h("h2", {}, car.model),
    h("p", { class: "muted" }, `${car.registration} · ${car.year} · ${car.fuel} · ${car.mileage_km?.toLocaleString("da-DK")} km · ${car.ownership}`),
    car.active_repair ? repairProgress(car.active_repair) : "",
    h("p", {}, "Næste booking: ", car.next_booking
      ? h("strong", {}, `${car.next_booking.date} kl. ${car.next_booking.time} · ${car.next_booking.workshop_name}`)
      : h("span", { class: "muted" }, "ingen")),
    h("p", {}, "Næste service: ", car.next_service_date ?? "–", " ", car.service_due_soon ? badge("snart", "warn") : ""),
    h("div", { class: "actions" },
      h("button", { onclick: () => showCar(car.id) }, "Biloplysninger"),
      h("button", { class: "secondary", onclick: () => startBooking(car.id) }, "Book værksted")))));
}

function repairProgress(repair) {
  return h("div", { class: "card" },
    h("strong", {}, `🔧 ${REPAIR_TEXT[repair.status]}`),
    h("div", { class: "progress" }, Array.from({ length: repair.steps }, (_, i) => h("span", { class: i < repair.step ? "done" : "" }))),
    h("div", { class: "muted" }, repair.description),
    repair.message ? h("div", {}, repair.message) : "",
    h("div", { class: "muted" }, `Forventet klar: ${repair.estimated_ready ?? "–"} · Opdateret ${formatDate(repair.updated_at)}`));
}

// ---------------------------------------------------------------- Biloplysninger
async function showCar(carId) {
  const d = await api(`/cars/${carId}/details`);
  const c = d.car;
  $("#car-details").replaceChildren(
    h("div", { class: "card highlight" },
      h("div", { class: "brand" }, c.brand),
      h("h2", {}, `${c.model} · ${c.registration}`),
      h("div", { class: "kpis" },
        info("Årgang", c.year), info("Drivmiddel", c.fuel), info("Kilometer", c.mileage_km?.toLocaleString("da-DK")),
        info("Ejerform", c.ownership), info("Stelnummer", c.vin ?? "–"), info("Næste service", c.next_service_date ?? "–")),
      c.active_repair ? repairProgress(c.active_repair) : "",
      h("button", { onclick: () => startBooking(c.id) }, "Book værksted")),
    h("div", { class: "grid wide" },
      h("div", { class: "card" }, h("h3", {}, "Servicehistorik"), h("div", { id: "service-table" })),
      h("div", { class: "card" }, h("h3", {}, "Dokumenter for bilen"), h("div", { id: "car-doc-table" }))),
  );
  renderTable($("#service-table"), d.service_history, [
    { label: "Dato", key: "date" },
    { label: "Type", key: "type" },
    { label: "Værksted", key: "workshop_name" },
    { label: "Km", class: "num", render: (s) => s.mileage_km?.toLocaleString("da-DK") ?? "–" },
    { label: "Pris", class: "num", render: (s) => formatKr(s.price) },
    { label: "Udført", key: "description" },
  ], "Ingen service registreret");
  renderTable($("#car-doc-table"), d.documents, [
    { label: "Dato", key: "date" }, { label: "Titel", key: "title" }, { label: "Kategori", render: (x) => badge(x.category) },
  ], "Ingen dokumenter");
  goTo("car");
}

function info(label, value) {
  return h("div", { class: "kpi" }, h("div", { class: "label" }, label), h("div", {}, h("strong", {}, value ?? "–")));
}

// ---------------------------------------------------------------- Værkstedsbooking (CRUD)
function startBooking(carId) {
  const form = $("#booking-form");
  form.reset();
  form.elements.id.value = "";
  form.elements.car_id.value = carId;
  $("#booking-title").textContent = "Book tid på værksted";
  $("#slots").replaceChildren();
  goTo("bookings");
}

function renderBookings() {
  const form = $("#booking-form");
  const cars = state.overview.cars;
  fillSelect(form.elements.car_id, cars, (c) => `${c.brand} ${c.model} (${c.registration})`);
  fillSelect(form.elements.workshop_id, state.workshops, (w) => `${w.name} – ${w.brands.replaceAll(",", ", ")}`);

  renderTable($("#booking-table"), state.overview.bookings, [
    { label: "Dato", render: (b) => `${b.date} kl. ${b.time}` },
    { label: "Bil", render: (b) => `${b.brand} ${b.model}` },
    { label: "Værksted", key: "workshop_name" },
    { label: "Type", key: "service_type" },
    { label: "Status", render: (b) => badge(b.status, BOOKING_BADGE[b.status]) },
    {
      label: "",
      render: (b) => b.status !== "BEKRÆFTET" ? "" : h("div", { class: "actions" },
        h("button", { class: "small secondary", onclick: () => editBooking(b) }, "Ret"),
        h("button", { class: "small secondary", onclick: () => cancelBooking(b) }, "Aflys"),
        h("button", { class: "small danger", onclick: () => deleteBooking(b) }, "Slet")),
    },
  ], "Ingen bookinger");
}

function editBooking(booking) {
  fillForm($("#booking-form"), booking);
  $("#booking-title").textContent = `Ret booking #${booking.id}`;
  loadSlots();
}

async function cancelBooking(booking) {
  await run(() => api(`/bookings/${booking.id}`, { method: "PUT", body: { status: "AFLYST" } }), "Bookingen er aflyst");
  loadAll();
}

async function deleteBooking(booking) {
  if (!confirm("Slet bookingen helt?")) return;
  await run(() => api(`/bookings/${booking.id}`, { method: "DELETE" }), "Bookingen er slettet");
  loadAll();
}

async function loadSlots() {
  const form = $("#booking-form");
  const { workshop_id: workshop, date } = formToJson(form);
  if (!workshop || !date) return;
  const slots = await api(`/available-times?workshop_id=${workshop}&date=${date}`);
  $("#slots").replaceChildren(...slots.map((s) => h("button", {
    type: "button",
    class: `small ${form.elements.time.value === s.time ? "" : "secondary"}`,
    disabled: !s.available && form.elements.time.value !== s.time,
    onclick: () => { form.elements.time.value = s.time; loadSlots(); },
  }, s.time)));
}

$("#booking-form [name=date]").addEventListener("change", loadSlots);
$("#booking-form [name=workshop_id]").addEventListener("change", loadSlots);

bindCrudForm($("#booking-form"), "bookings", () => {
  $("#booking-title").textContent = "Book tid på værksted";
  $("#slots").replaceChildren();
  loadAll();
});

// ---------------------------------------------------------------- Aftaler og dokumenter
function renderDocuments() {
  const category = $("#doc-filter [name=category]").value;
  const carName = Object.fromEntries(state.overview.cars.map((c) => [c.id, `${c.brand} ${c.model}`]));
  renderTable($("#document-table"), state.overview.documents.filter((d) => !category || d.category === category), [
    { label: "Dato", key: "date" },
    { label: "Titel", key: "title" },
    { label: "Kategori", render: (d) => badge(d.category) },
    { label: "Bil", render: (d) => carName[d.car_id] ?? "Generelt" },
    { label: "Beskrivelse", key: "description" },
  ], "Ingen dokumenter");
}

$("#doc-filter").addEventListener("change", renderDocuments);

// ---------------------------------------------------------------- Værksted (medarbejder)
async function loadWorkshop() {
  const [repairs, cars] = await Promise.all([api("/repairs"), api("/cars")]);
  const carName = Object.fromEntries(cars.map((c) => [c.id, `${c.brand} ${c.model} (${c.registration})`]));
  renderTable($("#repair-table"), repairs, [
    { label: "Bil", render: (r) => carName[r.car_id] },
    { label: "Reparation", key: "description" },
    {
      label: "Status",
      render: (r) => h("select", {
        onchange: async (e) => {
          await run(() => api(`/repairs/${r.id}`, { method: "PUT", body: { status: e.target.value } }), "Status opdateret");
          loadAll();
        },
      }, state.repairSteps.map((s) => h("option", { value: s, selected: s === r.status }, REPAIR_TEXT[s]))),
    },
    { label: "Opdateret", render: (r) => formatDate(r.updated_at) },
  ], "Ingen reparationer");
  for (const form of [$("#repair-form"), $("#service-form")]) {
    fillSelect(form.elements.car_id, cars, (c) => carName[c.id]);
  }
  fillSelect($("#service-form [name=workshop_id]"), state.workshops, (w) => w.name);
}

bindCrudForm($("#repair-form"), "repairs", loadAll);
bindCrudForm($("#service-form"), "service-history", loadAll);

// ---------------------------------------------------------------- Start
async function start() {
  const [customers, workshops, repairSteps] = await Promise.all([api("/customers"), api("/workshops"), api("/repair-steps")]);
  Object.assign(state, { workshops, repairSteps });
  fillSelect($("#customer-select"), customers, (c) => c.name);
  state.customerId = Number($("#customer-select").value);
  await loadAll();
}

$("#customer-select").addEventListener("change", (event) => {
  state.customerId = Number(event.target.value);
  loadAll();
});

setupTabs();
start().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
