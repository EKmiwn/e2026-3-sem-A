// GreenMobility Hotspot – administratorside (præsentationslag). Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { tab: "overview", caseId: null, staff: [] };

const RES_STATUS = { AKTIV: "ok", BENYTTET: "", ANNULLERET: "muted", UDLOEBET: "danger" };
const SPOT_STATUS = { LEDIG: "ok", RESERVERET: "warn", OPTAGET: "danger", SPAERRET: "muted" };
const CASE_TYPE = { KONTAKT: ["Chat", ""], PLADS_OPTAGET: ["Plads optaget", "danger"], KAN_IKKE_FINDE: ["Kan ikke finde plads", "warn"] };

// ---------------------------------------------------------------- Indlæsning
async function loadAll() {
  const [overview, spots, reservations, hotspots, events, customers, staff] = await Promise.all([
    api("/hotspots/overview"), api("/admin/spots"), api("/reservations"), api("/hotspots"),
    api("/events"), api("/customers"), api("/staff"),
  ]);
  state.staff = staff;
  renderOverview(overview, customers, events);
  renderSpots(spots);
  renderReservations(reservations);
  renderSetup(hotspots);
  renderStaff(staff);
  await loadCases();
}

// ---------------------------------------------------------------- Overblik
function renderOverview(overview, customers, events) {
  const sum = (key) => overview.reduce((total, row) => total + row[key], 0);
  const totals = { name: "I alt", total: sum("total"), free: sum("free"), reserved: sum("reserved"), occupied: sum("occupied"),
    blocked: sum("blocked"), active_reservations: sum("active_reservations"), consistent: overview.every((row) => row.consistent) };

  renderTable($("#count-table"), [...overview, totals], [
    { label: "Hotspot", render: (r) => r === totals ? h("strong", {}, r.name) : r.name },
    { label: "Ledige", key: "free", class: "num" },
    { label: "Reserveret", key: "reserved", class: "num" },
    { label: "Optaget", key: "occupied", class: "num" },
    { label: "Spærret", key: "blocked", class: "num" },
    { label: "I alt", key: "total", class: "num" },
    { label: "Aktive res.", key: "active_reservations", class: "num" },
    { label: "Stemmer", render: (r) => r.consistent ? h("span", { class: "check-ok" }, "✓") : h("span", { class: "check-bad" }, "✗ Afvigelse") },
  ]);

  renderTable($("#customer-table"), customers, [
    { label: "Kunde", key: "name" },
    { label: "Nummerplade", key: "car_plate" },
    { label: "", render: (c) => h("a", { class: "button secondary small", href: `./?kunde=${c.id}`, target: "_blank" }, "Åbn kundeside") },
  ]);

  $("#event-list").replaceChildren(...events.slice(0, 12).map((e) =>
    h("li", {}, h("strong", {}, e.event), " – ", e.message, h("div", { class: "muted" }, formatDate(e.occurred_at)))));
}

// ---------------------------------------------------------------- Pladser
function renderSpots(spots) {
  renderTable($("#spot-table"), spots, [
    { label: "Hotspot", key: "hotspot_name" },
    { label: "Plads", key: "label" },
    { label: "Status", render: (s) => badge(s.status, SPOT_STATUS[s.status]) },
    { label: "Reservation", render: (s) => s.active_reservation ?? "–" },
    { label: "Simulér", render: (s) => spotActions(s) },
  ]);
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

// ---------------------------------------------------------------- Reservationer
function renderReservations(reservations) {
  renderTable($("#all-reservations"), reservations, [
    { label: "Nr.", key: "reservation_no" },
    { label: "Kunde", key: "customer_name" },
    { label: "Hotspot / plads", render: (r) => `${r.hotspot_name} · ${r.spot_label}` },
    { label: "Frist", render: (r) => formatDate(r.arrival_deadline) },
    { label: "Status", render: (r) => badge(r.status, RES_STATUS[r.status]) },
    {
      label: "",
      render: (r) => r.status === "AKTIV"
        ? h("div", { class: "actions" },
            h("button", { class: "small secondary", onclick: () => adminPost(`/reservations/${r.id}/arrive`, "Ankomst registreret – pladsen er optaget") }, "Registrér ankomst"),
            h("button", { class: "small secondary", onclick: () => adminPost(`/admin/reservations/${r.id}/expire`, "Fristen er overskredet – reservationen er udløbet") }, "Simulér udløb"))
        : "",
    },
  ]);
}

// ---------------------------------------------------------------- Henvendelser og medarbejdere
async function loadCases() {
  const cases = await api("/support");
  const open = cases.filter((c) => c.status === "AABEN").length;
  $("#open-cases").replaceChildren(open ? badge(String(open), "danger") : "");

  $("#case-list").replaceChildren(...(cases.length ? cases.map((c) => {
    const [label, variant] = CASE_TYPE[c.type];
    return h("button", { class: c.id === state.caseId ? "active" : "", onclick: () => { state.caseId = c.id; loadCases(); } },
      h("strong", {}, `${c.case_no} · ${c.customer_name}`), " ", badge(label, variant), " ",
      c.status === "LUKKET" ? badge("Lukket", "muted") : "",
      h("span", { class: "sub" }, `${c.staff_name ?? "Ikke tildelt"} · ${c.messages.at(-1).text}`));
  }) : [h("p", { class: "empty" }, "Ingen henvendelser endnu")]));

  const current = cases.find((c) => c.id === state.caseId);
  $("#reply-form").hidden = !current || current.status === "LUKKET";
  $("#close-case").hidden = !current || current.status === "LUKKET";
  if (!current) return;
  $("#case-title").textContent = `${current.case_no} · ${current.customer_name}${current.reservation_no ? ` · ${current.reservation_no}` : ""}`;
  const chat = $("#case-chat");
  chat.replaceChildren(...current.messages.map((m) => h("div", { class: `msg ${{ KUNDE: "them", MEDARBEJDER: "me", SYSTEM: "system" }[m.sender]}` },
    m.sender === "KUNDE" ? h("span", { class: "who" }, current.customer_name) : null, m.text)));
  chat.scrollTop = chat.scrollHeight;
  const select = $("#reply-form [name=staff_id]");
  if (!select.options.length) fillSelect(select, state.staff, (s) => s.name);
  if (current.staff_id) select.value = current.staff_id;
}

$("#reply-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  await run(() => api(`/support/${state.caseId}/messages`, { method: "POST", body: { sender: "MEDARBEJDER", ...formToJson(form) } }));
  form.elements.text.value = "";
  loadCases();
});

$("#close-case").addEventListener("click", async () => {
  await run(() => api(`/support/${state.caseId}/close`, { method: "POST" }), "Henvendelsen er lukket");
  loadCases();
});

function renderStaff(staff) {
  renderTable($("#staff-table"), staff, [
    { label: "Navn", key: "name" },
    { label: "Rolle", key: "role" },
    { label: "Status", render: (s) => h("span", {}, h("span", { class: `dot ${s.online ? "on" : ""}` }), s.online ? " Online" : " Offline") },
    { label: "", render: (s) => h("button", { class: "small secondary", onclick: async () => {
        await run(() => api(`/staff/${s.id}`, { method: "PUT", body: { online: s.online ? 0 : 1 } }));
        loadAll();
      } }, s.online ? "Sæt offline" : "Sæt online") },
  ]);
}

// ---------------------------------------------------------------- Opsætning
function renderSetup(hotspots) {
  const hotspotForm = $("#hotspot-form");
  renderTable($("#hotspot-table"), hotspots, [
    { label: "Navn", key: "name" },
    { label: "Område", key: "area" },
    { label: "", render: (hs) => crudButtons("hotspots", hotspotForm, hs, loadAll) },
  ]);
  fillSelect($("#spot-form [name=hotspot_id]"), hotspots, (hs) => hs.name);
}

bindCrudForm($("#hotspot-form"), "hotspots", loadAll);
bindCrudForm($("#spot-form"), "spots", loadAll);

// ---------------------------------------------------------------- Start
setupTabs((tab) => { state.tab = tab; });
setInterval(() => { if (state.tab === "support") loadCases(); }, 5000);   // nye beskeder fra kunder
loadAll().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
