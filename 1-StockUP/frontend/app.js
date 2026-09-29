// StockUP – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.
// Klienten indeholder ingen forretningsregler: den spørger serveren og viser svaret.

const state = { dashboard: null, coffees: [], products: [] };

const SACK_STATUS = { PAA_LAGER: "ok", I_BRUG: "", REST: "warn", TOM: "muted" };

// ---------------------------------------------------------------- Indlæsning
async function loadAll() {
  const [dashboard, coffees, products, roasts, movements] = await Promise.all([
    api("/dashboard"),
    api("/green-coffees"),
    api("/products"),
    api("/roasts"),
    api("/movements"),
  ]);
  Object.assign(state, { dashboard, coffees, products });
  renderDashboard();
  renderRegisterForms();
  renderCatalog();
  renderRoasts(roasts);
  renderMovements(movements);
}

// ---------------------------------------------------------------- Dashboard
function renderDashboard() {
  const { kpis, sacks, products } = state.dashboard;
  $("#kpis").replaceChildren(
    kpi(kpis.sacks_in_stock, "sække på lager"),
    kpi(`${kpis.green_kg} kg`, "grønne bønner"),
    kpi(kpis.roasts_possible, "mulige ristninger"),
    kpi(kpis.bags_in_stock, "poser klar til salg"),
    kpi(kpis.products_low, "varer under minimum"),
  );

  renderTable($("#sack-table"), sacks, [
    { label: "Lot", key: "lot_number" },
    { label: "Råkaffe", render: (s) => `${s.coffee_name} (${s.origin})` },
    { label: "Modtaget", key: "received_date" },
    { label: "Tilbage", class: "num", render: (s) => `${s.remaining_kg} kg` },
    { label: "Ristninger", class: "num", key: "roasts_left" },
    { label: "Status", render: (s) => badge(s.status, SACK_STATUS[s.status]) },
    {
      label: "",
      render: (s) => s.status === "REST"
        ? h("button", { class: "small secondary", onclick: () => closeSack(s) }, "Afslut rest")
        : "",
    },
  ]);

  renderTable($("#product-table"), products, [
    { label: "SKU", key: "sku" },
    { label: "Vare", key: "name" },
    { label: "Pose", class: "num", render: (p) => `${p.bag_size_g} g` },
    { label: "På lager", class: "num", key: "stock_bags" },
    { label: "Min.", class: "num", key: "min_bags" },
    { label: "Salg/dag", class: "num", key: "sales_per_day" },
    { label: "Dækning", class: "num", render: (p) => (p.coverage_days === null ? "–" : `${p.coverage_days} dage`) },
    { label: "Status", render: (p) => badge(p.status, p.status === "LAV" ? "danger" : "ok") },
  ]);
}

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value), h("div", { class: "label" }, label));
}

async function closeSack(sack) {
  await run(() => api(`/sacks/${sack.id}/close`, { method: "POST" }), `Rest på ${sack.lot_number} afsluttet`);
  loadAll();
}

// ---------------------------------------------------------------- Registrering
function renderRegisterForms() {
  const roastable = state.dashboard.sacks.filter((s) => s.remaining_kg >= state.dashboard.rules.roast_kg);
  fillSelect($("#roast-form [name=sack_id]"), roastable,
    (s) => `${s.lot_number} · ${s.coffee_name} · ${s.remaining_kg} kg`);
  fillSelect($("#roast-form [name=product_id]"), state.dashboard.products,
    (p) => `${p.name} (${p.bag_size_g} g) – forslag ${p.suggested_bags} poser`);
  fillSelect($("#sale-form [name=product_id]"), state.dashboard.products,
    (p) => `${p.name} – ${p.stock_bags} på lager`);
  fillSelect($("#sack-form [name=green_coffee_id]"), state.coffees, (c) => `${c.name} (${c.origin})`);
}

function renderRoasts(roasts) {
  const sackLot = Object.fromEntries(state.dashboard.sacks.map((s) => [s.id, s.lot_number]));
  const productName = Object.fromEntries(state.products.map((p) => [p.id, p.name]));
  renderTable($("#roast-table"), roasts.slice(0, 10), [
    { label: "Tid", render: (r) => formatDate(r.roasted_at) },
    { label: "Sæk", render: (r) => sackLot[r.sack_id] ?? `#${r.sack_id}` },
    { label: "Vare", render: (r) => productName[r.product_id] },
    { label: "Kg", class: "num", key: "kg_used" },
    { label: "Poser", class: "num", key: "bags_produced" },
    { label: "Udført af", key: "performed_by" },
    {
      label: "",
      render: (r) => h("button", {
        class: "small secondary",
        onclick: async () => {
          await run(() => api(`/roasts/${r.id}`, { method: "DELETE" }), "Ristning fortrudt");
          loadAll();
        },
      }, "Fortryd"),
    },
  ]);
}

$("#roast-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const result = await run(
    () => api("/roasts", { method: "POST", body: formToJson(event.target) }),
    (r) => `Ristning registreret: ${r.sack.lot_number} har nu ${r.sack.remaining_kg} kg (${r.sack.status})`,
  );
  event.target.reset();
  loadAll();
  return result;
});

$("#sale-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await run(() => api("/sales", { method: "POST", body: formToJson(event.target) }),
    (r) => `Salg registreret – ${r.product.stock_bags} poser tilbage`);
  event.target.reset();
  loadAll();
});

$("#sack-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await run(() => api("/sacks", { method: "POST", body: formToJson(event.target) }),
    (s) => `Sæk ${s.lot_number} modtaget med ${s.remaining_kg} kg`);
  event.target.reset();
  loadAll();
});

// ---------------------------------------------------------------- Råkaffe og varer (CRUD)
function renderCatalog() {
  const coffeeForm = $("#coffee-form");
  const productForm = $("#product-form");
  fillSelect(productForm.elements.green_coffee_id, state.coffees, (c) => c.name, { placeholder: "Blanding (ingen)" });

  renderTable($("#coffee-table"), state.coffees, [
    { label: "Navn", key: "name" },
    { label: "Oprindelse", key: "origin" },
    { label: "Leverandør", key: "supplier" },
    { label: "Kr/kg", class: "num", key: "cost_per_kg" },
    { label: "", render: (c) => crudButtons("green-coffees", coffeeForm, c, loadAll) },
  ]);

  const coffeeName = Object.fromEntries(state.coffees.map((c) => [c.id, c.name]));
  renderTable($("#catalog-product-table"), state.products, [
    { label: "SKU", key: "sku" },
    { label: "Navn", key: "name" },
    { label: "Råkaffe", render: (p) => coffeeName[p.green_coffee_id] ?? "Blanding" },
    { label: "Pris", class: "num", render: (p) => formatKr(p.price) },
    { label: "", render: (p) => crudButtons("products", productForm, p, loadAll) },
  ]);
}

bindCrudForm($("#coffee-form"), "green-coffees", loadAll);
bindCrudForm($("#product-form"), "products", loadAll);

// ---------------------------------------------------------------- Bevægelser
function renderMovements(movements) {
  renderTable($("#movement-table"), movements, [
    { label: "Tid", render: (m) => formatDate(m.occurred_at) },
    { label: "Type", render: (m) => badge(m.movement_type) },
    { label: "Mængde", class: "num", render: (m) => `${m.quantity > 0 ? "+" : ""}${m.quantity} ${m.unit}` },
    { label: "Note", key: "note" },
  ]);
}

// ---------------------------------------------------------------- Start
setupTabs();
loadAll().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
