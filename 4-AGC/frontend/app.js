// AGC QC Informationshub – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { userId: null, users: [], categories: [], options: null, deliverableId: null };

const STATUS = { UDKAST: "warn", GODKENDT: "ok", FRAVALGT: "muted" };

// Prioritet og status vises med både tekst, symbol og farve – farve er aldrig den eneste markering (afsnit 14)
const PRIORITY = {
  "Business Critical": ["▲▲ Business Critical", "danger"],
  High: ["▲ High", "warn"],
  Normal: ["● Normal", ""],
  Low: ["▽ Low", "muted"],
};
const DELIVERABLE_STATUS = {
  "Ikke startet": ["○ Ikke startet", "muted"],
  "I gang": ["◐ I gang", ""],
  Afventer: ["… Afventer", "warn"],
  Blokeret: ["⛔ Blokeret", "danger"],
  Afsluttet: ["✓ Afsluttet", "ok"],
};

const priorityBadge = (p) => badge(...PRIORITY[p]);
const statusBadge = (s) => badge(...DELIVERABLE_STATUS[s]);
const responsible = (d) => [d.team_name, d.owner_name].filter(Boolean).join(" / ") || "–";

function formatDay(value) {
  return value ? new Date(`${value}T00:00`).toLocaleDateString("da-DK", { day: "2-digit", month: "2-digit", year: "numeric" }) : "–";
}

function deadlineCell(d) {
  return d.overdue
    ? h("span", { class: "overdue" }, formatDay(d.deadline), " ", badge("⚠ Overskredet", "danger"))
    : formatDay(d.deadline);
}

function currentUser() {
  return state.users.find((u) => String(u.id) === state.userId);
}

function goToTab(name) {
  document.querySelector(`.tabs button[data-tab="${name}"]`).click();
}

// Alle kald sender den valgte testbruger med (simuleret login)
function call(path, options = {}) {
  return api(path, { ...options, headers: { "X-User-Id": state.userId } });
}

// ---------------------------------------------------------------- Indlæsning
async function loadBase() {
  const [users, categories] = await Promise.all([api("/users"), api("/categories")]);
  Object.assign(state, { users, categories });
  const select = $("#user-select");
  fillSelect(select, users, (u) => `${u.name} (${u.role})`);
  state.userId = select.value;
  fillSelect($("#search-form [name=category_id]"), categories, (c) => c.name, { placeholder: "Alle" });
}

async function loadAll() {
  const user = currentUser();
  const noContent = "Administratorrollen giver ikke adgang til indhold.";
  if (user.role === "administrator") {
    ["#home-deliverables", "#home-info", "#deliverable-table"].forEach((s) => showRoleHint(s, noContent));
    $("#home-kpis").replaceChildren();
    $("#deliverable-form").hidden = true;
  }
  await Promise.allSettled([
    user.role !== "administrator" ? loadDeliverablesTab().then(loadHome) : null,
    user.role === "leder" ? loadReview() : showRoleHint("#review-table", "Til kontrol er for ledere."),
    user.role !== "administrator" ? search() : showRoleHint("#search-results", "Administratorrollen giver ikke adgang til indhold."),
    loadShared(),
    loadFeed(),
    loadAdmin(),
  ]);
}

function showRoleHint(selector, text) {
  $(selector).replaceChildren(h("p", { class: "empty" }, text));
}

// ---------------------------------------------------------------- Til kontrol
async function loadReview() {
  const rows = await call("/review-queue");
  renderTable($("#review-table"), rows, [
    { label: "Kilde", render: (i) => badge(i.system) },
    { label: "Titel", key: "title" },
    { label: "Forslag", render: (i) => badge(i.category_name, i.category_id ? "" : "warn") },
    { label: "v", class: "num", key: "version" },
    { label: "", render: (i) => h("button", { class: "small", onclick: () => showDetail(i.id) }, "Kontrollér") },
  ], "Ingen poster til kontrol 🎉");
}

async function showDetail(infoId, target = "#detail") {
  const { info, source, shares, history, can_edit, relevant_teams, deliverables } = await call(`/info/${infoId}`);
  const box = $(target);
  box.hidden = false;
  box.replaceChildren(...[
    h("h2", {}, info.title),
    h("p", {}, badge(info.status, STATUS[info.status]), " ", badge(`version ${info.version}`, "muted"), " ",
      badge(info.category_name, info.category_id ? "" : "warn")),
    h("p", {}, info.summary),
    h("p", { class: "muted" }, h("strong", {}, "Relevant for: "), relevant_teams.length ? relevant_teams.join(", ") : "ingen teams endnu"),
    deliverables.length
      ? h("p", { class: "muted" }, h("strong", {}, "Koblet til leverance: "),
          deliverables.map((d, n) => [n ? ", " : "", h("button", { class: "link", onclick: () => openDeliverable(d.id) }, d.title)]))
      : null,
    h("p", { class: "muted" }, h("strong", {}, "Hvorfor fanget: "), info.match_basis),
    h("h3", {}, `Originalkilde · ${source.system} ${source.external_id ?? ""}`),
    h("p", { class: "muted" }, `Fra ${source.sender ?? "–"}${source.channel ? ` i ${source.channel}` : ""} · ${formatDate(source.received_at)}`),
    h("blockquote", { class: "card" }, source.text),
  ].filter(Boolean));

  if (can_edit && target === "#detail") {
    const form = h("form", {},
      h("label", {}, "Titel", h("input", { name: "title", value: info.title })),
      h("label", {}, "Resumé", h("textarea", { name: "summary" }, info.summary)),
      h("label", {}, "Kategori", h("select", { name: "category_id", "data-number": true },
        h("option", { value: "" }, "Uklassificeret"),
        state.categories.map((c) => h("option", { value: c.id, selected: c.id === info.category_id }, c.name)))),
      h("div", { class: "actions" },
        h("button", {}, "Gem rettelse"),
        h("button", { type: "button", class: "secondary", onclick: () => act(infoId, "approve", "Version godkendt", info.version) }, "Godkend version"),
        h("button", { type: "button", class: "danger", onclick: () => act(infoId, "discard", "Posten er fravalgt") }, "Fravælg")),
    );
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const body = { ...formToJson(form), expected_version: info.version };
      if (!("category_id" in body)) body.category_id = null;
      await run(() => call(`/info/${infoId}`, { method: "PUT", body }), "Rettelse gemt som ny version – godkend igen");
      refreshAfterChange(infoId);
    });
    box.append(h("h3", {}, "Kontrollér og ret"), form);

    if (info.status === "GODKENDT") box.append(await shareForm(info));
  }

  box.append(
    h("h3", {}, "Delingshistorik"),
    shares.length
      ? h("ul", { class: "list" }, shares.map((s) => h("li", {}, `v${s.version} delt af ${s.sender_name} med ${s.recipients} · ${formatDate(s.shared_at)}`)))
      : h("p", { class: "empty" }, "Ikke delt endnu"),
    h("h3", {}, "Hændelser"),
    h("ul", { class: "list" }, history.map((e) => h("li", {}, h("strong", {}, e.type), ` – ${e.details ?? ""} `,
      h("span", { class: "muted" }, `${e.actor_name ?? "System"} · ${formatDate(e.occurred_at)}`)))),
  );
}

async function shareForm(info) {
  const recipients = await call(`/info/${info.id}/recipients`);
  const form = h("form", { class: "card" },
    h("h3", {}, "Del godkendt version med medarbejdere"),
    h("p", { class: "muted" }, `Forhåndsvisning: "${info.title}" – ${info.summary}`),
    h("fieldset", {}, recipients.map((u) =>
      h("label", {}, h("input", { type: "checkbox", name: "recipient_ids", value: u.id, "data-list": true }), u.name))),
    h("button", {}, "Del"),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const { recipient_ids } = formToJson(form);
    await run(() => call(`/info/${info.id}/share`, {
      method: "POST", body: { expected_version: info.version, recipient_ids: recipient_ids.map(Number) },
    }), (r) => `Delt med ${r.recipients} modtager(e)`);
    refreshAfterChange(info.id);
  });
  return form;
}

async function act(infoId, action, message, expectedVersion) {
  await run(() => call(`/info/${infoId}/${action}`, { method: "POST", body: { expected_version: expectedVersion } }), message);
  refreshAfterChange(infoId);
}

function refreshAfterChange(infoId) {
  loadAll();
  showDetail(infoId).catch(() => $("#detail").replaceChildren(h("p", { class: "empty" }, "Posten er ikke længere synlig.")));
}

// ---------------------------------------------------------------- Søg
async function search() {
  const query = new URLSearchParams(formToJson($("#search-form"))).toString();
  const rows = await call(`/info?${query}`);
  renderTable($("#search-results"), rows, [
    { label: "Modtaget", render: (i) => formatDate(i.received_at) },
    { label: "Kilde", render: (i) => badge(i.system) },
    { label: "Titel", key: "title" },
    { label: "Resumé", key: "summary" },
    { label: "Kategori", key: "category_name" },
    { label: "Status", render: (i) => badge(i.status, STATUS[i.status]) },
    { label: "Delinger", class: "num", key: "share_count" },
    { label: "", render: (i) => h("button", { class: "small", onclick: () => run(() => showDetail(i.id, "#search-detail")) }, "Åbn") },
  ], "Ingen resultater");
}

$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(search);
});

// ---------------------------------------------------------------- Leverancer & Prioritering
async function loadOptions() {
  const options = await call("/deliverable-options");
  state.options = options;
  const asRows = (values) => values.map((v) => ({ id: v, name: v }));
  const filter = $("#deliverable-filter");
  fillSelect(filter.elements.priority, asRows(options.priorities), (r) => r.name, { placeholder: "Alle" });
  fillSelect(filter.elements.status, asRows(options.statuses), (r) => r.name, { placeholder: "Alle" });
  fillSelect(filter.elements.team_id, options.teams, (t) => t.name, { placeholder: "Alle" });
  fillSelect(filter.elements.owner_id, options.people, (p) => p.name, { placeholder: "Alle" });

  const form = $("#deliverable-form");
  fillSelect(form.elements.priority, asRows(options.priorities), (r) => r.name);
  form.elements.priority.value = "Normal";
  fillSelect(form.elements.status, asRows(options.statuses), (r) => r.name);
  fillSelect(form.elements.team_id, options.teams, (t) => t.name, { placeholder: "– intet team –" });
  fillSelect(form.elements.owner_id, options.people, (p) => `${p.name}${p.team_name ? ` (${p.team_name})` : ""}`, { placeholder: "– ingen person –" });
  fillSelect(form.elements.info_id, options.infos, (i) => i.title, { placeholder: "– ingen –" });
  form.hidden = !options.can_edit;
  $("#deliverable-form-hint").hidden = options.can_edit;
  toggleBlockedReason();
}

async function loadDeliverablesTab() {
  await loadOptions();
  await loadDeliverables();
  if (state.deliverableId) openDeliverable(state.deliverableId, { switchTab: false }).catch(() => {});
}

async function loadDeliverables() {
  const filters = formToJson($("#deliverable-filter"));
  if (!filters.overdue) delete filters.overdue;
  const rows = await call(`/deliverables?${new URLSearchParams(filters)}`);
  renderDeliverables($("#deliverable-table"), rows, { editable: state.options.can_edit });
  return rows;
}

// F10, NF02, NF03: prioritet, ansvarlig, deadline og status i samme oversigt – vigtigste øverst
function renderDeliverables(container, rows, { editable = false, total } = {}) {
  if (!rows.length) {
    container.replaceChildren(h("p", { class: "empty" }, "Ingen leverancer matcher"));
    return;
  }
  const columns = [
    ["Prioritet", (d) => editable && d.status !== "Afsluttet" ? prioritySelect(d) : priorityBadge(d.priority)],
    ["Leverance", (d) => h("button", { class: "link", onclick: () => openDeliverable(d.id) }, d.title)],
    ["Ansvarlig", responsible],
    ["Deadline", deadlineCell],
    ["Status", (d) => statusBadge(d.status)],
  ];
  container.replaceChildren(h("div", { class: "table-wrap" }, h("table", {},
    h("thead", {}, h("tr", {}, columns.map(([label]) => h("th", {}, label)))),
    h("tbody", {}, rows.map((d) => h("tr", { class: d.priority === "Business Critical" && d.status !== "Afsluttet" ? "critical" : "" },
      columns.map(([, render]) => h("td", {}, render(d)))))),
  )));
  if (total > rows.length) container.append(h("p", { class: "muted" }, `Viser ${rows.length} af ${total} aktive leverancer`));
}

// F14: lederen ændrer prioritet direkte i oversigten, og rækkefølgen opdateres med det samme
function prioritySelect(d) {
  return h("select", {
    "aria-label": `Prioritet for ${d.title}`,
    onchange: async (event) => {
      try {
        await run(() => call(`/deliverables/${d.id}`, { method: "PUT", body: { priority: event.target.value, expected_version: d.version } }),
          `Prioritet ændret til ${event.target.value}`);
      } finally {
        refreshDeliverables(d.id);
      }
    },
  }, state.options.priorities.map((p) => h("option", { value: p, selected: p === d.priority }, PRIORITY[p][0])));
}

async function openDeliverable(id, { switchTab = true } = {}) {
  if (switchTab && !$("#tab-deliverables").classList.contains("active")) goToTab("deliverables");
  state.deliverableId = id;
  const { deliverable: d, comments, history, info, can_edit } = await call(`/deliverables/${id}`);
  const box = $("#deliverable-detail");
  const commentForm = h("form", {},
    h("label", {}, "Ny kommentar", h("textarea", { name: "text", required: true })),
    h("div", { class: "actions" }, h("button", {}, "Tilføj kommentar")));
  commentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitOnce(commentForm, () => call(`/deliverables/${id}/comments`, { method: "POST", body: formToJson(commentForm) }), "Kommentar tilføjet");
    openDeliverable(id, { switchTab: false });
  });

  box.replaceChildren(...[
    h("h2", {}, d.title),
    h("p", {}, priorityBadge(d.priority), " ", statusBadge(d.status), " ", d.overdue ? badge("⚠ Overskredet", "danger") : null),
    d.description ? h("p", {}, d.description) : null,
    h("dl", { class: "facts" },
      h("dt", {}, "Ansvarlig"), h("dd", {}, responsible(d)),
      h("dt", {}, "Deadline"), h("dd", {}, deadlineCell(d)),
      d.status === "Blokeret" ? [h("dt", {}, "Blokeret fordi"), h("dd", {}, d.blocked_reason)] : null,
      h("dt", {}, "Oprettet"), h("dd", {}, `${d.created_by_name} · ${formatDate(d.created_at)}`),
      d.closed_at ? [h("dt", {}, "Afsluttet"), h("dd", {}, formatDate(d.closed_at))] : null,
      h("dt", {}, "Information"), h("dd", {}, info
        ? h("button", { class: "link", onclick: () => { goToTab("search"); run(() => showDetail(info.id, "#search-detail")); } }, info.title)
        : d.info_id ? "Koblet til information, du ikke har adgang til" : "–"),
    ),
    can_edit ? h("div", { class: "actions" }, h("button", { class: "secondary", onclick: () => editDeliverable(d) }, "Redigér leverance")) : null,
    h("h3", { style: "margin-top:16px" }, "Kommentarer"),
    comments.length
      ? h("ul", { class: "list" }, comments.map((c) => h("li", {}, c.text, " ", h("span", { class: "muted" }, `– ${c.user_name} · ${formatDate(c.created_at)}`))))
      : h("p", { class: "empty" }, "Ingen kommentarer endnu"),
    commentForm,
    h("h3", { style: "margin-top:16px" }, "Historik"),
    h("ul", { class: "list" }, history.map((e) => h("li", {}, h("strong", {}, e.type), ` – ${e.details ?? ""} `,
      h("span", { class: "muted" }, `${e.actor_name ?? "System"} · ${formatDate(e.occurred_at)}`)))),
  ].filter(Boolean));
}

function editDeliverable(d) {
  const form = $("#deliverable-form");
  for (const field of form.elements) {
    if (field.name && field.name in d) field.value = d[field.name] ?? "";
  }
  $("#deliverable-form-title").textContent = `Redigér: ${d.title}`;
  toggleBlockedReason();
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

function resetDeliverableForm() {
  const form = $("#deliverable-form");
  form.reset();
  form.elements.id.value = "";
  form.elements.version.value = "";
  form.elements.priority.value = "Normal";
  $("#deliverable-form-title").textContent = "Opret leverance";
  toggleBlockedReason();
}

function toggleBlockedReason() {
  const form = $("#deliverable-form");
  const blocked = form.elements.status.value === "Blokeret";
  $("#blocked-reason").hidden = !blocked;
  form.elements.blocked_reason.required = blocked;
}

// NF07: knappen er låst, mens kaldet kører, så gentagne klik ikke giver dubletter
async function submitOnce(form, action, message) {
  const button = form.querySelector("button:not([type=button])");
  button.disabled = true;
  try {
    return await run(action, message);
  } finally {
    button.disabled = false;
  }
}

$("#deliverable-form").elements.status.addEventListener("change", toggleBlockedReason);
$("#deliverable-form [data-reset]").addEventListener("click", resetDeliverableForm);
$("#deliverable-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = formToJson(form);
  const fields = ["title", "description", "priority", "team_id", "owner_id", "deadline", "status", "blocked_reason", "info_id"];
  const body = Object.fromEntries(fields.map((f) => [f, data[f] ?? null]));
  const saved = data.id
    ? await submitOnce(form, () => call(`/deliverables/${data.id}`, { method: "PUT", body: { ...body, expected_version: data.version } }), "Leverancen er gemt")
    : await submitOnce(form, () => call("/deliverables", { method: "POST", body }), "Leverancen er oprettet");
  resetDeliverableForm();
  refreshDeliverables(saved.id);
});

$("#deliverable-filter").addEventListener("submit", (event) => {
  event.preventDefault();
  run(loadDeliverables);
});
$("#deliverable-filter [data-reset]").addEventListener("click", () => {
  $("#deliverable-filter").reset();
  run(loadDeliverables);
});

async function refreshDeliverables(id) {
  await Promise.allSettled([loadDeliverables().then(loadHome), openDeliverable(id, { switchTab: false })]);
}

// ---------------------------------------------------------------- Home / Informationshub
async function loadHome() {
  const [active, info] = await Promise.all([call("/deliverables"), call("/info")]);
  const count = (test) => active.filter(test).length;
  $("#home-kpis").replaceChildren(
    kpi(count((d) => d.priority === "Business Critical"), "▲▲ Business Critical"),
    kpi(count((d) => d.overdue), "⚠ Overskredne deadlines"),
    kpi(count((d) => d.status === "Blokeret"), "⛔ Blokerede"),
    kpi(active.length, "Aktive leverancer"),
  );
  renderDeliverables($("#home-deliverables"), active.slice(0, 5), { total: active.length });

  $("#home-categories").replaceChildren(...state.categories.map((c) =>
    h("button", { class: "small secondary", onclick: () => searchCategory(c.id) }, c.name)));
  const latest = info.slice(0, 5);
  $("#home-info").replaceChildren(latest.length
    ? h("ul", { class: "list" }, latest.map((i) => h("li", {},
        h("p", { style: "margin:0" }, badge(i.category_name), " ",
          i.status !== "GODKENDT" ? [badge(i.status, STATUS[i.status]), " "] : null,
          h("button", { class: "link", onclick: () => openInfo(i.id) }, i.title)),
        h("p", { class: "muted", style: "margin:0" }, `${i.summary} · ${formatDate(i.received_at)}`))))
    : h("p", { class: "empty" }, "Ingen information endnu"));
}

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value), h("div", { class: "label" }, label));
}

function openInfo(id) {
  goToTab("search");
  run(() => showDetail(id, "#search-detail"));
}

function searchCategory(categoryId) {
  const form = $("#search-form");
  form.reset();
  form.elements.category_id.value = categoryId;
  goToTab("search");
  run(search);
}

$("#home-search").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = $("#search-form");
  form.reset();
  form.elements.q.value = event.target.elements.q.value;
  goToTab("search");
  run(search);
});

document.querySelectorAll("[data-goto]").forEach((b) => b.addEventListener("click", () => goToTab(b.dataset.goto)));

// ---------------------------------------------------------------- Delt med mig
async function loadShared() {
  const rows = await call("/shared-with-me");
  $("#shared-list").replaceChildren(rows.length
    ? h("div", { class: "grid" }, rows.map((s) => h("div", { class: `card ${s.read_at ? "" : "highlight"}` },
        h("p", {}, badge(s.snapshot.category_name), " ", badge(s.snapshot.system, "muted")),
        h("h3", {}, s.snapshot.title),
        h("p", {}, s.snapshot.summary),
        h("p", { class: "muted" }, `Delt af ${s.sender_name} · ${formatDate(s.shared_at)} · version ${s.version}`),
        s.read_at
          ? h("p", { class: "muted" }, `Læst ${formatDate(s.read_at)}`)
          : h("button", {
              class: "small",
              onclick: async () => { await run(() => call(`/shares/${s.share_id}/read`, { method: "POST" }), "Markeret som læst"); loadShared(); },
            }, "Markér som læst"))))
    : h("p", { class: "empty" }, "Intet er delt med dig endnu"));
}

// ---------------------------------------------------------------- Kilder og testfeed
async function loadFeed() {
  const feed = await api("/feed");
  renderTable($("#feed-table"), feed, [
    { label: "System", key: "system" },
    { label: "Ekstern id", key: "external_id" },
    { label: "Emne", key: "title" },
    { label: "Status", render: (f) => badge(f.delivered ? "modtaget" : "venter", f.delivered ? "ok" : "muted") },
  ]);
  const events = await call("/events").catch(() => []);
  renderTable($("#event-table"), events.slice(0, 15), [
    { label: "Tid", render: (e) => formatDate(e.occurred_at) },
    { label: "Hændelse", key: "type" },
    { label: "Detaljer", key: "details" },
  ], "Kun ledere og administratorer kan se loggen");
}

$("#simulate-button").addEventListener("click", async () => {
  const result = await run(() => api("/connectors/simulate", { method: "POST" }), (r) =>
    r.duplicate ? "Dublet – posten blev ikke oprettet igen" : r.relevant ? "Relevant – lagt i Til kontrol" : "Ikke relevant – fravalgt og logget");
  $("#ingest-result").textContent = JSON.stringify(result, null, 2);
  loadAll();
});

$("#note-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await run(() => call("/notes", { method: "POST", body: formToJson(event.target) }), "Note oprettet og lagt i Til kontrol");
  event.target.reset();
  loadAll();
});

// ---------------------------------------------------------------- Administration
async function loadAdmin() {
  const [categories, access] = await Promise.all([api("/categories"), api("/category-access")]);
  state.categories = categories;
  const userName = Object.fromEntries(state.users.map((u) => [u.id, u.name]));
  const categoryName = Object.fromEntries(categories.map((c) => [c.id, c.name]));

  renderTable($("#category-table"), categories, [
    { label: "Navn", key: "name" },
    { label: "Nøgleord", key: "keywords" },
    { label: "", render: (c) => crudButtons("categories", $("#category-form"), c, loadAll) },
  ]);
  fillSelect($("#access-form [name=user_id]"), state.users, (u) => `${u.name} (${u.role})`);
  fillSelect($("#access-form [name=category_id]"), categories, (c) => c.name);
  renderTable($("#access-table"), access, [
    { label: "Bruger", render: (a) => userName[a.user_id] },
    { label: "Kategori", render: (a) => categoryName[a.category_id] },
    { label: "Rettighed", render: (a) => badge(a.permission, a.permission === "redigér" ? "ok" : "") },
    { label: "", render: (a) => crudButtons("category-access", $("#access-form"), a, loadAll) },
  ]);
}

bindCrudForm($("#category-form"), "categories", loadAll);
bindCrudForm($("#access-form"), "category-access", loadAll);

// ---------------------------------------------------------------- Start
$("#user-select").addEventListener("change", (event) => {
  state.userId = event.target.value;
  state.deliverableId = null;
  $("#detail").replaceChildren(h("p", { class: "empty" }, "Vælg en post for at kontrollere den mod kilden."));
  $("#deliverable-detail").replaceChildren(h("p", { class: "empty" }, "Vælg en leverance for at se detaljer, kommentarer og historik."));
  $("#search-detail").hidden = true;
  resetDeliverableForm();
  loadAll();
});

setupTabs();
loadBase()
  .then(loadAll)
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
