// JOE Pant – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { storeId: null, customerId: null, customers: [] };

const TYPE_BADGE = { PANT_BETALT: "", RETUR_GODKENDT: "ok", RETUR_AFVIST: "danger", POINT_INDLØST: "warn" };

// ---------------------------------------------------------------- Indlæsning
async function loadBase() {
  const [stores, drinks, customers] = await Promise.all([api("/stores"), api("/drinks"), api("/customers")]);
  state.customers = customers;
  fillSelect($("#store-select"), stores, (s) => `${s.name} (${s.location_type})`);
  state.storeId = Number($("#store-select").value);
  fillSelect($("#order-form [name=drink_id]"), drinks, (d) => `${d.name} – ${d.price} kr.`);
  fillSelect($("#order-form [name=customer_id]"), customers, (c) => c.name, { placeholder: "Ingen app (anonym)" });
  fillSelect($("#return-form [name=customer_id]"), customers, (c) => c.name, { placeholder: "Vælg konto" });
  const customerSelect = $("#customer-select");
  const previous = state.customerId;
  fillSelect(customerSelect, customers, (c) => c.name);
  if (previous) customerSelect.value = previous;
  state.customerId = Number(customerSelect.value);
}

async function loadAll() {
  await Promise.all([loadCups(), loadWallet(), loadReport(), loadSettings()]);
}

// ---------------------------------------------------------------- POS: salg
$("#order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { receipt: r } = await run(() => api("/orders", {
    method: "POST", body: { ...formToJson(event.target), store_id: state.storeId },
  }), "Kop udleveret");
  $("#receipt").replaceChildren(h("div", { class: "card highlight" },
    h("h3", {}, `Kvittering ${r.receipt_no}`),
    renderReceiptLine(r.drink, r.price),
    renderReceiptLine("Pant på kop", r.deposit),
    renderReceiptLine(h("strong", {}, "I alt"), h("strong", {}, `${r.total} kr.`)),
    h("p", {}, "Kop-kode: ", h("span", { class: "code" }, r.cup_code)),
    h("p", { class: "muted" }, r.message),
    r.customer ? badge(`Koblet til ${r.customer}`, "ok") : badge("Ikke koblet til app", "warn")));
  loadAll();
});

function renderReceiptLine(label, value) {
  return h("div", { style: "display:flex;justify-content:space-between" }, h("span", {}, label),
    h("span", {}, typeof value === "number" ? `${value} kr.` : value));
}

// ---------------------------------------------------------------- POS: retur
async function returnCup(body) {
  const box = $("#scan-result");
  try {
    const result = await api("/returns", { method: "POST", body: { ...body, store_id: state.storeId } });
    box.replaceChildren(h("div", { class: "scan-result ok" }, `✔ ${result.message}`));
    toast(result.message);
  } catch (err) {
    box.replaceChildren(h("div", { class: "scan-result error" }, `✖ ${err.message}`));
    toast(err.message, "error");
  }
  loadAll();
}

$("#return-form").addEventListener("submit", (event) => {
  event.preventDefault();
  returnCup(formToJson(event.target));
  event.target.reset();
});

async function loadCups() {
  const cups = await api("/cups?status=UDLEVERET");
  renderTable($("#cup-table"), cups, [
    { label: "Kode", render: (c) => h("span", { class: "code" }, c.code) },
    { label: "Udleveret", render: (c) => formatDate(c.issued_at) },
    { label: "", render: (c) => h("button", { class: "small secondary", onclick: () => { $("#return-form").elements.cup_code.value = c.code; } }, "Brug kode") },
  ], "Ingen kopper i omløb");
}

// ---------------------------------------------------------------- Kunde-app
async function loadWallet() {
  const w = await api(`/customers/${state.customerId}/wallet`);
  $("#wallet-kpis").replaceChildren(
    kpi(w.customer.points, "point"),
    kpi(`${w.points_value_kr} kr.`, "værdi i appen"),
    kpi(w.cups_to_return.length, "kopper at aflevere"),
    kpi(w.impact.cups_returned, w.impact.badge ?? "kopper returneret"),
  );
  renderTable($("#my-cups"), w.cups_to_return, [
    { label: "Kop", render: (c) => h("span", { class: "code" }, c.code) },
    { label: "Købt", render: (c) => `${c.store_name} · ${formatDate(c.issued_at)}` },
    { label: "Pant", class: "num", render: (c) => `${c.deposit} kr.` },
    { label: "", render: (c) => h("button", { class: "small", onclick: () => returnCup({ cup_code: c.code, customer_id: state.customerId }) }, "Scan for at aflevere") },
  ], "Ingen kopper at aflevere");
  renderTable($("#history"), w.history, [
    { label: "Tid", render: (t) => formatDate(t.created_at) },
    { label: "Hændelse", render: (t) => badge(t.type.replace("_", " "), TYPE_BADGE[t.type]) },
    { label: "Butik", key: "store_name" },
    { label: "Point", class: "num", render: (t) => (t.points ? `${t.points > 0 ? "+" : ""}${t.points}` : "–") },
  ]);
}

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value), h("div", { class: "label" }, label));
}

$("#customer-select").addEventListener("change", (event) => {
  state.customerId = Number(event.target.value);
  loadWallet();
});

$("#redeem-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await run(() => api(`/customers/${state.customerId}/redeem`, {
    method: "POST", body: { ...formToJson(event.target), store_id: state.storeId },
  }), (r) => `${r.points_used} point brugt – ${r.discount_kr} kr. i rabat`);
  event.target.reset();
  loadAll();
});

// ---------------------------------------------------------------- Bæredygtighedsrapport
async function loadReport() {
  const [r, transactions] = await Promise.all([api("/sustainability"), api("/transactions")]);
  $("#report-kpis").replaceChildren(
    kpi(r.cups_issued, "kopper udleveret"),
    kpi(r.cups_returned, "kopper returneret"),
    kpi(`${r.return_rate_pct} %`, "returrate"),
    kpi(r.cups_outstanding, "i omløb"),
    kpi(`${r.deposits_paid} kr.`, "pant opkrævet"),
    kpi(r.points_credited, "point krediteret"),
    kpi(r.cups_sold_without_app, "solgt uden app"),
  );
  renderTable($("#store-report"), r.per_store, [
    { label: "Butik", key: "name" },
    { label: "Type", key: "location_type" },
    { label: "Udleveret", class: "num", key: "issued" },
    { label: "Returneret her", class: "num", key: "returned_here" },
    { label: "Afviste scanninger", class: "num", key: "rejected" },
  ]);
  renderTable($("#transaction-table"), transactions.slice(0, 25), [
    { label: "Tid", render: (t) => formatDate(t.created_at) },
    { label: "Type", render: (t) => badge(t.type, TYPE_BADGE[t.type]) },
    { label: "Kop", key: "cup_code" },
    { label: "Kunde", key: "customer_name" },
    { label: "Butik", key: "store_name" },
    { label: "Beløb", class: "num", render: (t) => (t.amount ? `${t.amount} kr.` : "–") },
    { label: "Point", class: "num", key: "points" },
    { label: "Note", key: "note" },
  ]);
}

// ---------------------------------------------------------------- Indstillinger (CRUD)
async function loadSettings() {
  const [settings, drinks, customers] = await Promise.all([api("/settings"), api("/drinks"), api("/customers")]);
  renderTable($("#setting-table"), settings, [
    { label: "Nøgle", key: "key" },
    { label: "Værdi", class: "num", key: "value" },
    { label: "Beskrivelse", key: "description" },
    { label: "", render: (s) => h("button", { class: "small secondary", onclick: () => fillForm($("#setting-form"), s) }, "Redigér") },
  ]);
  renderTable($("#drink-table"), drinks, [
    { label: "Navn", key: "name" },
    { label: "Pris", class: "num", render: (d) => `${d.price} kr.` },
    { label: "", render: (d) => crudButtons("drinks", $("#drink-form"), d, reloadEverything) },
  ]);
  renderTable($("#customer-table"), customers, [
    { label: "Navn", key: "name" },
    { label: "E-mail", key: "email" },
    { label: "Point", class: "num", key: "points" },
    { label: "", render: (c) => crudButtons("customers", $("#customer-form"), c, reloadEverything) },
  ]);
}

function reloadEverything() {
  loadBase().then(loadAll);
}

bindCrudForm($("#setting-form"), "settings", reloadEverything);
bindCrudForm($("#drink-form"), "drinks", reloadEverything);
bindCrudForm($("#customer-form"), "customers", reloadEverything);

// ---------------------------------------------------------------- Start
$("#store-select").addEventListener("change", (event) => {
  state.storeId = Number(event.target.value);
});

setupTabs();
loadBase()
  .then(loadAll)
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
