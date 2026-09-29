// GreenMobility Hotspot – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { customerId: null, hotspots: [], reservations: [] };

const RES_STATUS = { AKTIV: "ok", BENYTTET: "", ANNULLERET: "muted", UDLOEBET: "danger" };
const SPOT_STATUS = { LEDIG: "ok", RESERVERET: "warn", OPTAGET: "danger", SPAERRET: "muted" };

// ---------------------------------------------------------------- Indlæsning
async function loadCustomers() {
  const customers = await api("/customers");
  const select = $("#customer-select");
  fillSelect(select, customers, (c) => `${c.name} (${c.car_plate})`);
  state.customerId = Number(select.value);
}

async function loadAll() {
  const [hotspots, reservations] = await Promise.all([
    api("/hotspots/overview"),
    api(`/reservations?customer_id=${state.customerId}`),
  ]);
  Object.assign(state, { hotspots, reservations });
  renderHotspots();
  renderMine();
  loadAdmin();
}

// ---------------------------------------------------------------- Kunde
function activeReservation() {
  return state.reservations.find((r) => r.status === "AKTIV");
}

function renderHotspots() {
  const active = activeReservation();
  $("#active-banner").replaceChildren(active
    ? h("div", { class: "card highlight" },
        h("strong", {}, `Du har en aktiv reservation: ${active.reservation_no} – plads ${active.spot_label} ved ${active.hotspot_name}. `),
        `Ankom senest kl. ${active.arrival_deadline.slice(11, 16)}.`)
    : "");

  $("#hotspot-cards").replaceChildren(...state.hotspots.map((hs) =>
    h("div", { class: "card" },
      h("h3", {}, hs.name),
      h("p", { class: "muted" }, hs.address),
      h("div", { class: "kpi" },
        h("div", { class: "value" }, hs.free),
        h("div", { class: "label" }, `ledige af ${hs.total} pladser`)),
      h("p", {}, badge(`${hs.reserved} reserveret`, "warn"), " ", badge(`${hs.occupied} optaget`, "danger")),
      h("button", { disabled: !hs.free || !!active, onclick: () => reserve(hs) },
        hs.free ? "Reservér plads" : "Ingen ledige pladser"),
    )));
}

async function reserve(hotspot) {
  const r = await run(
    () => api("/reservations", { method: "POST", body: { customer_id: state.customerId, hotspot_id: hotspot.id } }),
    (r) => `Reservation ${r.reservation_no} bekræftet – plads ${r.spot_label}`,
  );
  await loadAll();
  document.querySelector('[data-tab="mine"]').click();
  return r;
}

function renderMine() {
  const active = activeReservation();
  $("#active-reservation").replaceChildren(active
    ? h("div", { class: "card highlight" },
        h("h2", {}, `Reservation ${active.reservation_no}`),
        h("div", { class: "kpis" },
          info("Hotspot", active.hotspot_name),
          info("Plads", active.spot_label),
          info("Ankomstfrist", active.arrival_deadline.slice(11, 16)),
          info("Tid tilbage", h("span", { id: "countdown" }, countdown(active.arrival_deadline)))),
        h("div", { class: "actions" },
          h("button", { onclick: () => act(active, "arrive", "Ankomst registreret – god parkering!") }, "Jeg er ankommet"),
          h("button", { class: "danger", onclick: () => act(active, "cancel", "Reservationen er annulleret") }, "Annullér")))
    : h("div", { class: "card" }, h("p", { class: "empty" }, "Du har ingen aktiv reservation. Vælg et hotspot for at reservere.")));

  renderTable($("#my-reservations"), state.reservations, [
    { label: "Nr.", key: "reservation_no" },
    { label: "Hotspot", key: "hotspot_name" },
    { label: "Plads", key: "spot_label" },
    { label: "Oprettet", render: (r) => formatDate(r.created_at) },
    { label: "Frist", render: (r) => formatDate(r.arrival_deadline) },
    { label: "Status", render: (r) => badge(r.status, RES_STATUS[r.status]) },
  ], "Ingen reservationer endnu");
}

function info(label, value) {
  return h("div", { class: "kpi" }, h("div", { class: "label" }, label), h("div", { class: "value" }, value));
}

function countdown(deadline) {
  const ms = new Date(deadline.replace(" ", "T")) - Date.now();
  if (ms <= 0) return "Udløbet";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

// Opdaterer nedtællingen hvert sekund og henter ny status, når fristen er nået
setInterval(() => {
  const active = activeReservation();
  const el = $("#countdown");
  if (!active || !el) return;
  el.textContent = countdown(active.arrival_deadline);
  if (el.textContent === "Udløbet") loadAll();
}, 1000);

async function act(reservation, action, message) {
  await run(() => api(`/reservations/${reservation.id}/${action}`, { method: "POST" }), message);
  loadAll();
}

// ---------------------------------------------------------------- Administrator
async function loadAdmin() {
  const [spots, reservations, hotspots, events] = await Promise.all([
    api("/admin/spots"), api("/reservations"), api("/hotspots"), api("/events"),
  ]);

  renderTable($("#spot-table"), spots, [
    { label: "Hotspot", key: "hotspot_name" },
    { label: "Plads", key: "label" },
    { label: "Status", render: (s) => badge(s.status, SPOT_STATUS[s.status]) },
    { label: "Reservation", render: (s) => s.active_reservation ?? "–" },
    { label: "Simulér", render: (s) => spotActions(s) },
  ]);

  renderTable($("#all-reservations"), reservations, [
    { label: "Nr.", key: "reservation_no" },
    { label: "Kunde", key: "customer_name" },
    { label: "Hotspot / plads", render: (r) => `${r.hotspot_name} · ${r.spot_label}` },
    { label: "Frist", render: (r) => formatDate(r.arrival_deadline) },
    { label: "Status", render: (r) => badge(r.status, RES_STATUS[r.status]) },
    {
      label: "",
      render: (r) => r.status === "AKTIV"
        ? h("button", { class: "small secondary", onclick: () => adminPost(`/admin/reservations/${r.id}/expire`, "Fristen er overskredet – reservationen er udløbet") }, "Simulér udløb")
        : "",
    },
  ]);

  const hotspotForm = $("#hotspot-form");
  renderTable($("#hotspot-table"), hotspots, [
    { label: "Navn", key: "name" },
    { label: "Område", key: "area" },
    { label: "", render: (hs) => crudButtons("hotspots", hotspotForm, hs, loadAll) },
  ]);
  fillSelect($("#spot-form [name=hotspot_id]"), hotspots, (hs) => hs.name);

  $("#event-list").replaceChildren(...events.slice(0, 12).map((e) =>
    h("li", {}, h("strong", {}, e.event), " – ", e.message, h("div", { class: "muted" }, formatDate(e.occurred_at)))));
}

function spotActions(spot) {
  const buttons = [];
  if (spot.status === "OPTAGET") buttons.push(["Bil kører", () => adminPost(`/admin/spots/${spot.id}/depart`, `Plads ${spot.label} er ledig igen`)]);
  if (spot.status === "LEDIG") {
    buttons.push(["Bil parkerer", () => adminPost(`/admin/spots/${spot.id}/occupy`, `Plads ${spot.label} er optaget`)]);
    buttons.push(["Spær", () => setSpotStatus(spot, "SPAERRET")]);
  }
  if (spot.status === "SPAERRET") buttons.push(["Ophæv spærring", () => setSpotStatus(spot, "LEDIG")]);
  return h("div", { class: "actions" }, buttons.map(([label, fn]) => h("button", { class: "small secondary", onclick: fn }, label)));
}

async function adminPost(path, message) {
  await run(() => api(path, { method: "POST" }), message);
  loadAll();
}

async function setSpotStatus(spot, status) {
  await run(() => api(`/spots/${spot.id}`, { method: "PUT", body: { status } }), `Plads ${spot.label}: ${status}`);
  loadAll();
}

bindCrudForm($("#hotspot-form"), "hotspots", loadAll);
bindCrudForm($("#spot-form"), "spots", loadAll);

// ---------------------------------------------------------------- Start
$("#customer-select").addEventListener("change", (event) => {
  state.customerId = Number(event.target.value);
  loadAll();
});

setupTabs();
loadCustomers()
  .then(loadAll)
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
