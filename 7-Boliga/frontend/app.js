// Boliga Insight Hub – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { userId: null, propertyId: null };

const RISK = { lav: "ok", middel: "warn", høj: "danger" };
const HELP = {
  liggetid: "Liggetid er antal dage, boligen har været til salg.",
  ai: "Boligas AI-vurdering er en statistisk model med ca. 6,6 % usikkerhed.",
};

function goTo(tab) {
  document.querySelector(`.tabs [data-tab="${tab}"]`).click();
}

function kpi(value, label, help) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value),
    h("div", { class: "label" }, help ? h("abbr", { title: help }, label) : label));
}

// ---------------------------------------------------------------- Søg
async function search() {
  const params = new URLSearchParams(formToJson($("#search-form")));
  const properties = await api(`/properties/search?${params}`);
  $("#results").replaceChildren(...properties.map((p) => h("div", { class: "card" },
    h("h3", {}, p.address),
    h("p", { class: "muted" }, `${p.postcode} ${p.city} · ${p.property_type} · ${p.size_m2} m² · ${p.rooms ?? "?"} vær.`),
    h("p", {}, h("strong", {}, formatKr(p.list_price)), h("span", { class: "muted" }, ` · ${formatKr(p.price_per_m2)}/m²`)),
    h("p", {}, badge(`${p.days_on_market} dage til salg`, "muted"), " ",
      p.total_price_drop > 0 ? badge(`Prisfald ${p.total_price_drop_pct} %`, "warn") : "", " ",
      p.sales_channel === "Selvsalg" ? badge("Selvsalg") : ""),
    h("div", { class: "actions" },
      h("button", { onclick: () => openHub(p.id) }, "Åbn Insight Hub"),
      h("button", { class: "secondary", onclick: () => saveProperty(p.id) }, "Gem")))));
}

$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(search);
});

async function saveProperty(propertyId) {
  await run(() => api(`/users/${state.userId}/saved`, { method: "POST", body: { property_id: propertyId } }), "Boligen er gemt");
  loadSaved();
}

// ---------------------------------------------------------------- Insight Hub
async function openHub(propertyId) {
  state.propertyId = propertyId;
  const ctx = await api(`/properties/${propertyId}/insight`);
  const { property: p, market: m, dingeo: g, auctions } = ctx;
  goTo("hub");

  $("#hub").replaceChildren(
    h("div", { class: "card highlight" },
      h("h2", {}, `${p.address}, ${p.postcode} ${p.city}`),
      h("p", {}, h("strong", {}, "AI-resumé: "), ctx.ai_summary)),

    // Overblik først (progressiv disclosure) – detaljer ved klik
    h("div", { class: "kpis" },
      kpi(formatKr(p.list_price), "udbudspris"),
      kpi(formatKr(p.ai_valuation), `AI-vurdering (${p.valuation_diff_pct > 0 ? "+" : ""}${p.valuation_diff_pct} %)`, HELP.ai),
      kpi(`${formatKr(p.price_per_m2)}`, `pr. m² (område: ${m.avg_price_per_m2 ? formatKr(m.avg_price_per_m2) : "–"})`),
      kpi(`${p.days_on_market} dage`, `liggetid (område: ${m.avg_days_on_market ?? "–"})`, HELP.liggetid),
      kpi(p.energy_label ?? "–", `energimærke · bygget ${p.built_year ?? "?"}`)),

    h("div", { class: "grid wide" },
      h("div", {},
        h("details", { class: "card", open: true },
          h("summary", {}, "DinGeo: risiko og nabolag"),
          g ? h("ul", { class: "list" },
            h("li", {}, "Oversvømmelse ", badge(g.flood_risk, RISK[g.flood_risk])),
            h("li", {}, "Skybrud ", badge(g.cloudburst_risk, RISK[g.cloudburst_risk])),
            h("li", {}, "Radon ", badge(g.radon_risk, RISK[g.radon_risk])),
            h("li", {}, `Vejstøj: ${g.noise_db} dB`),
            h("li", {}, `Skole ${g.school_m} m · Station ${g.station_m} m · Dagligvarer ${g.grocery_m} m · Grønt område ${g.green_area_m} m`),
            h("li", {}, `Indbrudsindeks ${g.burglary_index} (100 = landsgennemsnit) · Bredbånd ${g.broadband_mbit} Mbit`))
            : h("p", { class: "empty" }, "Ingen DinGeo-data")),
        h("details", { class: "card" },
          h("summary", {}, `Prishistorik (${p.price_changes.length} ændringer)`),
          h("ul", { class: "list" }, p.price_changes.map((c) =>
            h("li", {}, `${c.changed_date}: ${formatKr(c.old_price)} → ${formatKr(c.new_price)}`)))),
        h("details", { class: "card" },
          h("summary", {}, `Solgte boliger i ${p.postcode} (${m.sales.length})`),
          h("ul", { class: "list" }, m.sales.map((s) =>
            h("li", {}, `${s.address}: ${formatKr(s.price)} · ${s.size_m2} m² · ${s.days_on_market} dage · ${s.sold_date}`)))),
        h("details", { class: "card" },
          h("summary", {}, `Tvangsauktioner i ${p.postcode} (${auctions.length})`),
          auctions.length
            ? h("ul", { class: "list" }, auctions.map((a) => h("li", {}, `${a.address} – ${a.auction_date} · mindstebud ${formatKr(a.min_bid)}`)))
            : h("p", { class: "empty" }, "Ingen kommende auktioner"))),
      chatPanel()),
  );
  loadConversation();
}

// ---------------------------------------------------------------- AI-sparringspartner
function chatPanel() {
  const form = h("form", { class: "toolbar" },
    h("input", { name: "question", required: true, placeholder: "Spørg fx: Er prisen for høj?", style: "flex:1" }),
    h("button", {}, "Spørg"));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = form.elements.question.value;
    form.reset();
    await run(() => api(`/properties/${state.propertyId}/ask`, { method: "POST", body: { user_id: state.userId, question } }));
    loadConversation();
  });
  return h("div", { class: "card" },
    h("h3", {}, "Spørg AI-sparringspartneren"),
    h("p", { class: "muted" }, "Svarene bygger kun på boligens data og viser kilderne. Samtalen gemmes, så du kan finde den igen."),
    h("div", { class: "chat", id: "chat" }),
    h("div", { class: "actions" }, ["Er prisen for høj?", "Hvorfor så lang liggetid?", "Risiko for oversvømmelse?", "Skoler og transport?"]
      .map((q) => h("button", { class: "small secondary", type: "button", onclick: () => { form.elements.question.value = q; form.requestSubmit(); } }, q))),
    form);
}

async function loadConversation() {
  const { messages } = await api(`/conversations?user_id=${state.userId}&property_id=${state.propertyId}`);
  const chat = $("#chat");
  if (!chat) return;
  chat.replaceChildren(...(messages.length
    ? messages.map((m) => h("div", { class: `bubble ${m.role}` }, m.text, m.sources ? h("small", {}, `Kilder: ${m.sources}`) : ""))
    : [h("p", { class: "empty" }, "Stil dit første spørgsmål om boligen.")]));
  chat.scrollTop = chat.scrollHeight;
}

// ---------------------------------------------------------------- Gemte og sammenlign
async function loadSaved() {
  const saved = await api(`/users/${state.userId}/saved`);
  renderTable($("#saved-list"), saved, [
    { label: "", render: (s) => h("input", { type: "checkbox", class: "compare-check", value: s.property_id }) },
    { label: "Adresse", render: (s) => `${s.property.address}, ${s.property.city}` },
    { label: "Pris", class: "num", render: (s) => formatKr(s.property.list_price) },
    { label: "Note", key: "note" },
    {
      label: "",
      render: (s) => h("div", { class: "actions" },
        h("button", { class: "small secondary", onclick: () => openHub(s.property_id) }, "Åbn"),
        h("button", {
          class: "small danger",
          onclick: async () => { await run(() => api(`/users/${state.userId}/saved/${s.property_id}`, { method: "DELETE" }), "Fjernet"); loadSaved(); },
        }, "Fjern")),
    },
  ], "Ingen gemte boliger endnu");
}

$("#compare-button").addEventListener("click", async () => {
  const ids = [...document.querySelectorAll(".compare-check:checked")].map((c) => c.value).join(",");
  const rows = await run(() => api(`/compare?ids=${ids}`));
  const fields = [
    ["Pris", (r) => formatKr(r.property.list_price)],
    ["m²", (r) => r.property.size_m2],
    ["Pris pr. m²", (r) => formatKr(r.property.price_per_m2)],
    ["Områdets m²-pris", (r) => formatKr(r.area_avg_price_per_m2)],
    ["AI-vurdering", (r) => `${formatKr(r.property.ai_valuation)} (${r.property.valuation_diff_pct} %)`],
    ["Liggetid", (r) => `${r.property.days_on_market} dage`],
    ["Energimærke", (r) => r.property.energy_label],
    ["Oversvømmelse", (r) => badge(r.dingeo.flood_risk, RISK[r.dingeo.flood_risk])],
    ["Skybrud", (r) => badge(r.dingeo.cloudburst_risk, RISK[r.dingeo.cloudburst_risk])],
    ["Støj", (r) => `${r.dingeo.noise_db} dB`],
    ["Skole / station", (r) => `${r.dingeo.school_m} m / ${r.dingeo.station_m} m`],
    ["Resumé", (r) => r.ai_summary],
  ];
  renderTable($("#compare-table"), fields.map(([label, fn]) => ({ label, fn })), [
    { label: "", render: (f) => h("strong", {}, f.label) },
    ...rows.map((r) => ({ label: r.property.address, render: (f) => f.fn(r) })),
  ]);
});

// ---------------------------------------------------------------- Admin (CRUD)
async function loadAdmin() {
  const properties = await api("/properties");
  renderTable($("#property-table"), properties, [
    { label: "Adresse", key: "address" },
    { label: "By", render: (p) => `${p.postcode} ${p.city}` },
    { label: "Pris", class: "num", render: (p) => formatKr(p.list_price) },
    { label: "", render: (p) => crudButtons("properties", $("#property-form"), p, () => { loadAdmin(); search(); }) },
  ]);
}

bindCrudForm($("#property-form"), "properties", () => { loadAdmin(); search(); });

// ---------------------------------------------------------------- Start
async function start() {
  const users = await api("/users");
  fillSelect($("#user-select"), users, (u) => u.name);
  state.userId = Number($("#user-select").value);
  await Promise.all([search(), loadSaved(), loadAdmin()]);
}

$("#user-select").addEventListener("change", (event) => {
  state.userId = Number(event.target.value);
  loadSaved();
  if (state.propertyId) loadConversation();
});

setupTabs();
start().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
