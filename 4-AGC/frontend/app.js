// AGC QC Informationshub – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { userId: null, users: [], categories: [] };

const STATUS = { UDKAST: "warn", GODKENDT: "ok", FRAVALGT: "muted" };

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
  const user = state.users.find((u) => String(u.id) === state.userId);
  await Promise.allSettled([
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

async function showDetail(infoId) {
  const { info, source, shares, history, can_edit } = await call(`/info/${infoId}`);
  const box = $("#detail");
  box.replaceChildren(
    h("h2", {}, info.title),
    h("p", {}, badge(info.status, STATUS[info.status]), " ", badge(`version ${info.version}`, "muted"), " ",
      badge(info.category_name, info.category_id ? "" : "warn")),
    h("p", { class: "muted" }, h("strong", {}, "Hvorfor fanget: "), info.match_basis),
    h("h3", {}, `Originalkilde · ${source.system} ${source.external_id ?? ""}`),
    h("p", { class: "muted" }, `Fra ${source.sender ?? "–"}${source.channel ? ` i ${source.channel}` : ""} · ${formatDate(source.received_at)}`),
    h("blockquote", { class: "card" }, source.text),
  );

  if (can_edit) {
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
  ], "Ingen resultater");
}

$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(search);
});

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
  $("#detail").replaceChildren(h("p", { class: "empty" }, "Vælg en post for at kontrollere den mod kilden."));
  loadAll();
});

setupTabs();
loadBase()
  .then(loadAll)
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
