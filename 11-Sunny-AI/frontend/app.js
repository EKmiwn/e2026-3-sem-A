// Sunny AI – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.
// Alle tal kommer fra backendens planmotor. Frontenden beregner ingen nøgletal selv.

const state = { userId: null, tab: "overview", status: null, plan: null, requestIds: {} };

// Samme labels, ikoner og farver på alle skærme (N01)
const LINE_STATUS = {
  "planlagt": ["✓ Planlagt", "ok"],
  "dækket af lager": ["✓ Dækket af lager", "ok"],
  "delvist planlagt": ["⚠ Delvist planlagt", "warn"],
  "blokeret": ["⛔ Blokeret", "danger"],
};
const PLAN_STATUS = {
  draft: ["Forslag – ikke godkendt", "warn"],
  approved: ["✓ Godkendt", "ok"],
  stale: ["Forældet", "muted"],
  preview: ["Foreløbig beregning – ikke gemt", "muted"],
};
const LEVEL = { fejl: ["⛔ Kræver kontrol", "danger"], advarsel: ["⚠ Advarsel", "warn"] };

// Demobrugeren sendes med som navn på godkendelser – det er ikke et login
function call(path, options = {}) {
  return api(path, { ...options, headers: { "X-User-Id": state.userId } });
}

// ---------------------------------------------------------------- Formatering (dansk, N11)
// Mængder kommer i tusindedele af basisenheden: 40000 L-tusindedele = 40 L
function qty(milli, unit) {
  if (milli === null || milli === undefined) return "ukendt";
  return `${(milli / 1000).toLocaleString("da-DK", { maximumFractionDigits: 3 })} ${unit ?? "(ukendt enhed)"}`;
}

function duration(minutes) {
  const hours = Math.floor(minutes / 60), rest = minutes % 60;
  return rest ? `${hours} t ${rest} min` : `${hours} t`;
}

function day(date) {
  return new Date(`${date}T12:00`).toLocaleDateString("da-DK", { weekday: "short", day: "2-digit", month: "2-digit" });
}

function longDate(date) {
  return new Date(`${date}T12:00`).toLocaleDateString("da-DK", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function isoWeek(date) {
  const d = new Date(`${date}T12:00`);
  d.setDate(d.getDate() + 3 - ((d.getDay() + 6) % 7));
  const firstThursday = new Date(d.getFullYear(), 0, 4);
  return 1 + Math.round(((d - firstThursday) / 86400000 - 3 + ((firstThursday.getDay() + 6) % 7)) / 7);
}

function statusBadge(map, key) {
  const [text, variant] = map[key] ?? [key, "muted"];
  return badge(text, variant);
}

function requestId() {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function goTo(tab) {
  document.querySelector(`.tabs button[data-tab="${tab}"]`).click();
}

// ---------------------------------------------------------------- Datastatus-banner (F01, alle skærme)
async function loadStatus() {
  const s = await api("/status");
  state.status = s;
  const control = s.kraever_kontrol;
  $("#status-banner").replaceChildren(
    badge("Demo", "muted"),
    h("span", {}, s.kilde),
    h("span", {}, "Data fra ", h("strong", {}, formatDate(s.snapshot.source_updated_at)), ` (snapshot #${s.snapshot.id})`),
    h("span", {}, "Beregnet ", formatDate(s.beregningstidspunkt)),
    s.foraeldet ? badge(`⛔ Data er ${Math.round(s.alder_timer)} t gamle – forældet`, "danger") : badge("✓ Friske data", "ok"),
    control ? badge(`⚠ ${control} forhold kræver kontrol`, "warn") : badge("✓ Intet kræver kontrol", "ok"),
    ...(s.advarsler ? [badge(`${s.advarsler} advarsel(er)`, "muted")] : []),
  );
}

// ---------------------------------------------------------------- Overblik
async function loadOverview() {
  const o = await api("/overview");
  const n = o.noegletal;
  const kpi = (value, label) => h("div", { class: "kpi" }, h("div", { class: "value" }, value), h("div", { class: "label" }, label));
  $("#kpis").replaceChildren(
    kpi(n.ordrer_i_plan, "Ordrer til planlægning"),
    kpi(n.raavarer_i_mangel, "Råvarer der mangler"),
    kpi(duration(n.planlagte_minutter), `Planlagte timer af ${duration(n.kapacitet_minutter)}`),
    kpi(o.status.kraever_kontrol, "Forhold der kræver kontrol"),
  );
  $("#overview-plan-label").textContent = `· uge ${isoWeek(o.uge_start)} · ${o.plan.label}`;
  const plan = await api(`/plans/current?uge_start=${o.uge_start}`);
  $("#overview-week").replaceChildren(weekGrid(plan));

  const list = $("#overview-actions");
  list.replaceChildren(...(o.handlinger.length ? o.handlinger.map((a) => h("li", {},
    h("div", { class: "text" }, statusBadge(LEVEL, a.niveau), " ", h("strong", {}, a.titel), h("div", { class: "muted" }, a.besked)),
    a.ordrelinje_id
      ? h("button", { class: "small secondary", onclick: () => { goTo("stock"); showOrder(a.ordrelinje_id); } }, "Åbn")
      : a.vare_id ? h("button", { class: "small secondary", onclick: () => { goTo("stock"); showItem(a.vare_id); } }, "Åbn") : null,
  )) : [h("li", { class: "empty" }, "Intet kræver handling.")]));
}

// ---------------------------------------------------------------- Ugeplan (F06–F12)
function weekGrid(plan, { interactive = false } = {}) {
  const r = plan.resultat;
  const risky = new Set(r.advarsler.map((a) => a.ordrelinje_id));
  return h("div", { class: "week" }, r.dage.map((d) => {
    const lines = r.planlinjer.filter((p) => p.dato === d.dato);
    const pct = d.kapacitet ? Math.min(100, Math.round((d.brugt / d.kapacitet) * 100)) : 0;
    return h("div", { class: "day" },
      h("h3", {}, day(d.dato)),
      h("div", { class: "cap" }, d.fortid ? "Før beregningsdato" : `${duration(d.brugt)} af ${duration(d.kapacitet)}`,
        d.manuel ? " · manuel" : ""),
      h("div", { class: "bar" }, h("span", { style: `width:${pct}%` })),
      lines.length ? lines.map((p) => h(interactive ? "button" : "div", {
        class: `plan-line ${risky.has(p.ordrelinje_id) ? "risk" : ""}`,
        type: interactive ? "button" : null,
        onclick: interactive ? () => explain(p.ordrelinje_id) : null,
      }, h("strong", {}, `Ordre ${p.ordre_id}`), h("div", { class: "hint" }, `${qty(p.maengde, p.enhed)} ${p.varenummer} · ${duration(p.minutter)}`)))
        : h("p", { class: "empty" }, "Ingen produktion"),
    );
  }));
}

// Uden valgt uge bruger backenden ugen for beregningstidspunktet
async function loadPlanTab(week) {
  const uge = week || $("#plan-form [name=uge_start]").value;
  const plan = await call(`/plans/current${uge ? `?uge_start=${uge}` : ""}`);
  const [orders, versions] = await Promise.all([api("/orders"), api(`/plans?uge_start=${plan.uge_start}`)]);
  state.plan = plan;
  fillPlanForm(plan.uge_start, plan, orders);
  renderPlan(plan);
  renderVersions(versions);
}

function fillPlanForm(uge, plan, orders) {
  const form = $("#plan-form");
  form.elements.uge_start.value = uge;
  const params = plan.parametre ?? {};
  const selected = params.ordrelinje_ids ? new Set(params.ordrelinje_ids) : null;
  const prio = params.prioritet ?? {};

  $("#plan-orders").replaceChildren(...orders.map((o) => {
    const open = o.status === "åben";
    return h("div", { class: "toolbar", style: "margin:0 0 6px" },
      h("label", {}, h("span", {},
        h("input", { type: "checkbox", name: "line", value: o.id, checked: open && (!selected || selected.has(o.id)), disabled: !open }),
        ` ${o.ordre_id} · ${qty(o.rest, o.enhed)} ${o.varenavn} · frist ${longDate(o.leveringsdato)}`,
        o.saesonmaerke ? " · sæson" : "", open ? "" : ` · ${o.status} (kan ikke planlægges)`)),
      open ? h("label", {}, h("span", { class: "hint" }, "Prioritet"),
        h("select", { name: `prio-${o.id}`, "data-source": o.prioritet, "aria-label": `Prioritet for ${o.ordre_id}` },
          ["normal", "høj"].map((p) => h("option", { selected: (prio[o.id] ?? o.prioritet) === p }, p)))) : null,
    );
  }));

  $("#plan-capacity").replaceChildren(...plan.resultat.dage.map((d) => h("label", {}, day(d.dato),
    h("input", { type: "number", name: `cap-${d.dato}`, min: 0, max: 24, step: 0.25, value: d.kapacitet / 60,
      "aria-label": `Timer ${day(d.dato)}` }))));
}

function readPlanForm() {
  const form = $("#plan-form");
  const body = { uge_start: form.elements.uge_start.value, ordrelinje_ids: [], kapacitet: {}, prioritet: {} };
  form.querySelectorAll("[name=line]:checked").forEach((c) => body.ordrelinje_ids.push(Number(c.value)));
  form.querySelectorAll("[name^=prio-]").forEach((s) => {
    if (s.value !== s.dataset.source) body.prioritet[s.name.slice(5)] = s.value;
  });
  form.querySelectorAll("[name^=cap-]").forEach((i) => { body.kapacitet[i.name.slice(4)] = Math.round(Number(i.value) * 60); });
  return body;
}

function renderPlan(plan) {
  const r = plan.resultat;
  const card = $("#plan-card");
  // replaceChildren() ville skrive null som tekst, så de valgfrie dele filtreres fra
  card.replaceChildren(...[
    h("div", { class: "toolbar", style: "justify-content:space-between" },
      h("h2", { style: "margin:0" }, `Uge ${isoWeek(r.uge_start)} · ${plan.label}`),
      statusBadge(PLAN_STATUS, plan.status)),
    plan.status === "stale" ? h("p", { class: "muted" }, `Forældet: ${plan.foraeldet_grund}. Beregn et nyt forslag.`) : null,
    plan.status === "preview" ? h("p", { class: "muted" }, "Beregnet med standardparametre. Tryk “Beregn forslag” for at gemme en planversion, der kan godkendes.") : null,
    plan.manuelle_parametre?.length ? h("p", {}, plan.manuelle_parametre.map((m) => [badge(`Manuel: ${m}`, "warn"), " "])) : null,
    h("p", { class: "hint" }, `Snapshot #${r.snapshot_id} · beregnet ${formatDate(r.beregningstidspunkt)}. Vælg en planlinje for at se beregningsgrundlaget.`),
    weekGrid(plan, { interactive: true }),
  ].filter(Boolean));

  if (r.uplanlagte.length) {
    const box = h("div", { style: "margin-top:16px" }, h("h3", {}, "Ikke planlagt"));
    renderTable(box.appendChild(h("div")), r.uplanlagte, [
      { label: "Ordre", key: "ordre_id" },
      { label: "Status", render: (u) => statusBadge(LINE_STATUS, u.status) },
      { label: "Ikke planlagt", class: "num", render: (u) => qty(u.uplanlagt_maengde, u.enhed) },
      { label: "Årsag", render: (u) => u.aarsager.map((a) => a.besked).join(" ") },
      { label: "", render: (u) => h("button", { class: "small secondary", onclick: () => explain(u.ordrelinje_id) }, "Vis grundlag") },
    ]);
    card.append(box);
  }
  if (r.advarsler.length) {
    card.append(h("h3", {}, "Advarsler"), h("ul", { class: "list" }, r.advarsler.map((a) =>
      h("li", {}, badge(`⚠ ${a.tekst}`, "warn"), ` Ordre ${a.ordre_id}: ${a.besked}`))));
  }
  card.append(approvalBox(plan));

  renderTable($("#needs-table"), r.raavarebehov, [
    { label: "Råvare", render: (n) => `${n.varenummer} ${n.navn}` },
    { label: "Behov", class: "num", render: (n) => qty(n.behov, n.enhed) },
    { label: "Heraf uplanlagt", class: "num", render: (n) => qty(n.behov_uplanlagt, n.enhed) },
    { label: "Disponibelt", class: "num", render: (n) => n.disponibelt === null ? badge("⚠ Uafklaret", "warn") : qty(n.disponibelt, n.enhed) },
    { label: "Mangel", class: "num", render: (n) => n.mangel === null ? "ukendt" : n.mangel ? badge(`⛔ ${qty(n.mangel, n.enhed)}`, "danger") : badge("✓ 0", "ok") },
  ], "Ingen råvarebehov");
}

function approvalBox(plan) {
  const box = h("div", { class: "card", style: "margin:16px 0 0" }, h("h3", {}, "Beslutning"));
  box.append(h("p", { class: "hint" }, "Godkendelse gemmer kun en lokal beslutning i Sunny AI. Der oprettes ingen produktionsordre i Uniconta, og “godkendt” betyder ikke, at produktionen er gennemført."));

  if (plan.status === "approved") {
    box.append(
      h("p", {}, badge("✓ Godkendt", "ok"), ` af ${plan.godkendt_af} · ${formatDate(plan.godkendt_at)}`, plan.delvis ? " · delvis godkendelse" : ""),
      h("a", { href: `${API_BASE}/api/plans/${plan.id}/calendar.ics`, download: "" }, "Hent kalenderfil (.ics) med godkendte planlinjer"),
    );
    return box;
  }
  if (plan.status !== "draft") {
    box.append(h("p", { class: "muted" }, plan.status === "preview"
      ? "Et foreløbigt forslag kan ikke godkendes. Beregn først en planversion."
      : "En forældet version kan ikke godkendes som aktuel."));
    return box;
  }

  const unplanned = plan.resultat.uplanlagte;
  const form = h("form", {},
    unplanned.length ? h("label", { style: "color:var(--text)" }, h("span", {},
      h("input", { type: "checkbox", name: "accepter_uplanlagte" }),
      ` Jeg accepterer, at ${unplanned.map((u) => u.ordre_id).join(", ")} ikke er planlagt (delvis godkendelse)`)) : null,
    h("div", { class: "actions" }, h("button", {}, `Godkend ${plan.label.toLowerCase()}`)),
  );
  state.requestIds[plan.id] ??= requestId();   // samme id ved dobbeltklik → én godkendelse (R08)
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    try {
      await run(() => call(`/plans/${plan.id}/approve`, {
        method: "POST",
        body: { request_id: state.requestIds[plan.id], accepter_uplanlagte: form.elements.accepter_uplanlagte?.checked ?? false },
      }), "Planversionen er godkendt");
      refresh();
    } catch {
      button.disabled = false;
    }
  });
  box.append(form);
  return box;
}

function explain(lineId) {
  const line = state.plan.resultat.linjer.find((l) => l.ordrelinje_id === lineId);
  const card = $("#explain-card");
  if (!line) {
    card.replaceChildren(h("h2", {}, "Beregningsgrundlag"), h("p", { class: "empty" }, "Ordren indgår ikke i planen."));
    return;
  }
  card.replaceChildren(
    h("h2", {}, `Beregningsgrundlag · ordre ${line.ordre_id}`),
    h("p", {}, statusBadge(LINE_STATUS, line.status), " ", line.aarsager.map((a) => [badge(a.kode, a.kode === "DEADLINE_RISK" ? "warn" : "danger"), " "])),
    h("div", { class: "table-wrap" }, h("table", {}, h("tbody", {},
      [["Vare", `${line.varenummer} ${line.varenavn}`],
        ["Kilde-id", line.kilde_id],
        ["Leveringsfrist", longDate(line.leveringsdato) + (line.forfalden ? " (overskredet)" : "")],
        ["Prioritet", line.prioritet + (line.prioritet_manuel ? " (manuel)" : "") + (line.saeson_aktiv ? " · sæson" : "")],
        ["Restmængde", qty(line.rest, line.enhed)],
        ["Lagerfradrag", qty(line.lagerfradrag_maengde, line.enhed) + (line.lagerfradrag.length ? ` (${line.lagerfradrag.map((b) => b.batchnummer).join(", ")})` : "")],
        ["Produktionsmængde", qty(line.produktionsbehov, line.enhed)],
        ["Råvarebehov", line.raavarebehov.map((r) => `${qty(r.behov, r.enhed)} ${r.varenummer}`).join(", ") || "ukendt"],
        ["Rate", line.rate ? `${line.rate} ${line.enhed}/time` : "ukendt"],
        ["Tidsforbrug", duration(line.minutter)],
      ].map(([k, v]) => h("tr", {}, h("th", {}, k), h("td", {}, v)))))),
    h("div", { class: "explain" }, h("h3", {}, "Forklaring"), h("ul", {}, line.forklaring.map((f) => h("li", {}, f)))),
    h("details", { class: "explain" }, h("summary", {}, "Anvendte antagelser"), h("ul", {}, state.plan.resultat.antagelser.map((a) => h("li", {}, a)))),
  );
  card.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderVersions(versions) {
  renderTable($("#versions-table"), versions, [
    { label: "Version", key: "versionsnummer" },
    { label: "Status", render: (v) => statusBadge(PLAN_STATUS, v.status) },
    { label: "Snapshot", render: (v) => `#${v.snapshot_id}` },
    { label: "Oprettet", render: (v) => formatDate(v.oprettet_at) },
    { label: "Manuelle parametre", render: (v) => v.manuelle_parametre.join(" · ") || "–" },
    { label: "Godkendt", render: (v) => v.godkendt_at ? `${v.godkendt_af} · ${formatDate(v.godkendt_at)}${v.delvis ? " (delvis)" : ""}` : "–" },
    { label: "Forældet fordi", render: (v) => v.foraeldet_grund ?? "–" },
    { label: "", render: (v) => h("button", { class: "small secondary", onclick: () => showVersion(v.id) }, "Vis") },
  ], "Ingen gemte versioner for ugen endnu");
}

async function showVersion(planId) {
  state.plan = await call(`/plans/${planId}`);
  renderPlan(state.plan);
  $("#plan-card").scrollIntoView({ behavior: "smooth" });
}

$("#plan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const plan = await run(() => call("/plans", { method: "POST", body: readPlanForm() }), (p) => `${p.label} beregnet`);
  await loadStatus();
  await loadPlanTab(plan.uge_start);
});

$("#plan-defaults").addEventListener("click", async () => {
  const uge = $("#plan-form [name=uge_start]").value;
  const [plan, orders] = await Promise.all([api(`/plans/current?uge_start=${uge}`), api("/orders")]);
  fillPlanForm(uge, { resultat: { dage: plan.resultat.dage.map((d) => ({ ...d, kapacitet: 480 })) } }, orders);
});

$("#plan-form [name=uge_start]").addEventListener("change", (event) => run(() => loadPlanTab(event.target.value)));

// ---------------------------------------------------------------- Lager og ordrer (F03–F05)
async function loadStock() {
  const q = encodeURIComponent($("#search-form [name=q]").value.trim());
  const [orders, stock] = await Promise.all([api(`/orders?q=${q}`), api(`/stock?q=${q}`)]);
  renderTable($("#orders-table"), orders, [
    { label: "Ordre", render: (o) => h("button", { class: "small secondary", onclick: () => showOrder(o.id) }, o.ordre_id) },
    { label: "Vare", render: (o) => `${o.varenummer} ${o.varenavn}` },
    { label: "Rest", class: "num", render: (o) => qty(o.rest, o.enhed) },
    { label: "Frist", render: (o) => longDate(o.leveringsdato) },
    { label: "Status", render: (o) => badge(o.status, o.status === "åben" ? "" : "muted") },
    { label: "Prioritet", render: (o) => o.prioritet + (o.saesonmaerke ? " · sæson" : "") },
  ], "Ingen ordrer matcher søgningen");
  renderTable($("#stock-table"), stock, [
    { label: "Vare", render: (b) => h("button", { class: "small secondary", onclick: () => showItem(b.vare_id) }, b.varenummer) },
    { label: "Navn", key: "varenavn" },
    { label: "Batch", key: "batchnummer" },
    { label: "Fysisk", class: "num", render: (b) => qty(b.fysisk_maengde, b.enhed) },
    { label: "Disponibel", class: "num", render: (b) => qty(b.disponibel, b.enhed) },
    { label: "Udløb", render: (b) => b.udloebsdato ? longDate(b.udloebsdato) : "ukendt" },
    { label: "Status", render: (b) => b.spaerret_grund ? badge(`⛔ ${b.spaerret_grund}`, "danger")
      : b.udloeb_snart ? badge("⚠ Udløber snart", "warn") : badge("✓ Klar", "ok") },
  ], "Ingen varer matcher søgningen");
}

function detailTable(rows) {
  return h("div", { class: "table-wrap" }, h("table", {}, h("tbody", {},
    rows.map(([k, v]) => h("tr", {}, h("th", {}, k), h("td", {}, v ?? "–"))))));
}

async function showOrder(lineId) {
  const d = await api(`/orders/${lineId}`);
  const o = d.ordrelinje;
  const f = d.forklaring;
  $("#detail-card").replaceChildren(...[
    h("h2", {}, `Ordre ${o.ordre_id}`),
    f ? h("p", {}, statusBadge(LINE_STATUS, f.status), " ", f.aarsager.map((a) => a.tekst).join(", ")) : null,
    detailTable([
      ["Vare", `${o.varenummer} ${o.varenavn}`],
      ["Bestilt / leveret", `${qty(o.bestilt_maengde, o.enhed)} / ${qty(o.leveret_maengde, o.enhed)}`],
      ["Restmængde", qty(o.rest, o.enhed)],
      ["Leveringsdato", longDate(o.leveringsdato)],
      ["Status", o.status],
      ["Prioritet", o.prioritet + (o.saesonmaerke ? " · sæsonmærket" : "")],
      ["Kilde-id", o.kilde_id],
      ["Kildeopdatering", `${formatDate(o.source_updated_at)} (snapshot #${o.snapshot_id})`],
      ["Råvare pr. enhed", d.ressourcebehov.map((r) => `${qty(r.maengde_pr_enhed, r.enhed)} ${r.varenummer}`).join(", ") || "ukendt"],
    ]),
    f ? h("div", { class: "explain" }, h("h3", {}, `Beregning i ${d.plan.label.toLowerCase()}`),
      h("ul", {}, f.forklaring.map((x) => h("li", {}, x)))) : null,
  ].filter(Boolean));
  $("#detail-card").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function showItem(itemId) {
  const d = await api(`/items/${itemId}/details`);
  const v = d.vare;
  $("#detail-card").replaceChildren(
    h("h2", {}, `${v.varenummer} ${v.navn}`),
    detailTable([
      ["Type", v.type],
      ["Basisenhed", v.basisenhed ?? "mangler"],
      ["Disponibelt", d.usikker ? badge("⚠ Uafklaret færdigmelding – intet sikkert tal", "warn") : qty(d.disponibelt, v.basisenhed)],
      ["Produktionsrate", d.rate ? `${d.rate} ${v.basisenhed}/time` : "–"],
      ["Kildeopdatering", `${formatDate(d.snapshot.source_updated_at)} (snapshot #${d.snapshot.id})`],
    ]),
    h("h3", {}, "Batches"),
    h("div", { id: "item-batches" }),
    h("h3", {}, "Ordrer"),
    h("div", { id: "item-orders" }),
  );
  renderTable($("#item-batches"), d.batches, [
    { label: "Batch", key: "batchnummer" },
    { label: "Fysisk", class: "num", render: (b) => qty(b.fysisk_maengde, b.enhed) },
    { label: "Reserveret", class: "num", render: (b) => qty(b.reserveret_maengde, b.enhed) },
    { label: "Udløb", render: (b) => b.udloebsdato ? longDate(b.udloebsdato) : "ukendt" },
    { label: "Kvalitet", key: "kvalitetsstatus" },
    { label: "Status", render: (b) => b.spaerret_grund ? badge(`⛔ ${b.spaerret_grund}`, "danger") : badge("✓ Klar", "ok") },
  ], "Ingen batches");
  renderTable($("#item-orders"), d.ordrer, [
    { label: "Ordre", render: (o) => h("button", { class: "small secondary", onclick: () => showOrder(o.id) }, o.ordre_id) },
    { label: "Vare", key: "varenummer" },
    { label: "Rest", class: "num", render: (o) => qty(o.rest, o.enhed) },
    { label: "Frist", render: (o) => longDate(o.leveringsdato) },
  ], "Ingen ordrer bruger varen");
  $("#detail-card").scrollIntoView({ behavior: "smooth", block: "start" });
}

$("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(loadStock);
});
$("#search-clear").addEventListener("click", () => {
  $("#search-form [name=q]").value = "";
  run(loadStock);
});

// ---------------------------------------------------------------- Spørg Sunny AI (F13, F14)
const EXAMPLES = [
  "Kan ordre O2 produceres?",
  "Kan ordre O1 produceres?",
  "Hvor meget R1 har vi?",
  "Hvor meget æble har vi?",
  "Hvilke råvarer mangler?",
  "Hvordan ser ugeplanen ud?",
  "Kan ordre O9 produceres?",
  "Hvordan færdigmelder jeg i Uniconta?",
];

async function ask(question, vareId) {
  const chat = $("#chat");
  chat.querySelector(".empty")?.remove();
  chat.prepend(h("div", { class: "bubble q" }, question));
  let a;
  try {
    a = await run(() => call("/assistant", { method: "POST", body: { spoergsmaal: question, vare_id: vareId } }));
  } catch (err) {
    chat.children[0].after(h("div", { class: "bubble" }, badge("Fejl", "danger"), ` Intet svar: ${err.message}`));
    return;
  }
  const variant = { ikke_fundet: "warn", uden_for_data: "muted", vaelg: "warn" }[a.type];
  chat.children[0].after(h("div", { class: "bubble" },
    variant ? h("p", { style: "margin:0 0 6px" }, badge({ ikke_fundet: "Ikke fundet", uden_for_data: "Uden for tilgængelige data", vaelg: "Vælg vare" }[a.type], variant)) : null,
    h("div", {}, a.svar),
    a.valg ? h("div", { class: "actions", style: "margin-top:8px" }, a.valg.map((v) =>
      h("button", { class: "small secondary", onclick: () => ask(`${question} (${v.label})`, v.vare_id) }, v.label))) : null,
    a.kilder.length ? h("div", { class: "actions", style: "margin-top:8px" }, a.kilder.map((k) =>
      h("button", { class: "small secondary", onclick: () => openSource(k) }, `Kilde: ${k.label}`))) : null,
    h("div", { class: "meta" }, `${a.assistent} · data fra ${formatDate(a.snapshot_tidspunkt)} (snapshot #${a.snapshot_id}) · ${a.plan.label}`),
  ));
}

function openSource(source) {
  if (source.type === "ordre") { goTo("stock"); showOrder(source.id); }
  else if (source.type === "vare") { goTo("stock"); showItem(source.id); }
  else if (source.type === "plan") goTo("plan");
  else goTo("data");
}

$("#ask-examples").replaceChildren(...EXAMPLES.map((q) => h("button", { class: "small secondary", onclick: () => ask(q) }, q)));
$("#ask-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = event.target.elements.spoergsmaal;
  ask(input.value.trim());
  input.value = "";
});

// ---------------------------------------------------------------- Datastatus (F01, F02, F04, F15)
async function loadData() {
  const [s, validation, snapshots, events, stock, items] = await Promise.all([
    api("/status"), api("/validation"), api("/snapshots"), api("/events"), api("/stock"), api("/items"),
  ]);
  $("#snapshot-info").replaceChildren(detailTable([
    ["Kilde", s.kilde],
    ["Snapshot", `#${s.snapshot.id} · ${s.snapshot.beskrivelse ?? ""}`],
    ["source", s.snapshot.source],
    ["Kilde opdateret", formatDate(s.snapshot.source_updated_at)],
    ["Indlæst", formatDate(s.snapshot.imported_at)],
    ["Schemaversion", s.snapshot.schema_version],
    ["Alder", [`${s.alder_timer} timer `, s.foraeldet ? badge("⛔ Forældet", "danger") : badge("✓ Frisk", "ok")]],
  ]));
  $("#clock-form [name=beregningstidspunkt]").value = s.beregningstidspunkt.replace(" ", "T");

  renderTable($("#problems-table"), validation.problemer, [
    { label: "Niveau", render: (p) => statusBadge(LEVEL, p.niveau) },
    { label: "Problem", key: "besked" },
    { label: "Hvad kan du gøre?", key: "handling" },
  ], "Ingen kendte dataproblemer ✓");

  fillSelect($("#import-expire [name=batchnummer]"), stock, (b) => `${b.batchnummer} · ${b.varenummer} ${b.varenavn}`, { valueKey: "batchnummer" });
  fillSelect($("#import-unresolved [name=vare_id]"), items.filter((i) => i.type === "råvare").concat(items.filter((i) => i.type !== "råvare")),
    (i) => `${i.varenummer} ${i.navn}`);
  fillSelect($("#import-order [name=vare_id]"), items.filter((i) => i.type === "færdigvare"), (i) => `${i.varenummer} ${i.navn}`);

  renderTable($("#snapshots-table"), snapshots, [
    { label: "#", key: "id" },
    { label: "Kilde opdateret", render: (x) => formatDate(x.source_updated_at) },
    { label: "Beskrivelse", key: "beskrivelse" },
  ]);
  renderTable($("#events-table"), events.slice(0, 20), [
    { label: "Tid", render: (e) => formatDate(e.timestamp) },
    { label: "Hændelse", key: "type" },
    { label: "Detaljer", key: "detaljer" },
    { label: "Aktør", key: "actor" },
  ]);
}

async function importSnapshot(body, message) {
  await run(() => call("/source/import", { method: "POST", body }), message);
  refresh();
}

$("#import-reload").addEventListener("submit", (event) => {
  event.preventDefault();
  importSnapshot({ type: "genindlaes" }, "Nyt snapshot indlæst – eksisterende planer er forældede");
});
$("#import-expire").addEventListener("submit", (event) => {
  event.preventDefault();
  importSnapshot({ type: "udloeb_batch", ...formToJson(event.target) }, "Batchen er registreret som udløbet i et nyt snapshot");
});
$("#import-unresolved").addEventListener("submit", (event) => {
  event.preventDefault();
  importSnapshot({ type: "uafklaret_faerdigmelding", ...formToJson(event.target) }, "Uafklaret færdigmelding registreret");
});
$("#import-resolve").addEventListener("click", () => importSnapshot({ type: "afklar" }, "Færdigmeldinger afklaret i et nyt snapshot"));
$("#import-order").addEventListener("submit", (event) => {
  event.preventDefault();
  importSnapshot({ type: "ny_ordre", ...formToJson(event.target) }, "Ny ordre indlæst");
  event.target.reset();
});

$("#clock-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = event.target.elements.beregningstidspunkt.value.replace("T", " ");
  await run(() => call("/clock", { method: "PUT", body: { beregningstidspunkt: value } }), "Beregningstidspunkt ændret – genberegn planen");
  refresh();
});

$("#reset-button").addEventListener("click", async () => {
  if (!confirm("Nulstil demoen? Alle planer, godkendelser og simulerede ændringer slettes.")) return;
  await run(() => api("/reset", { method: "POST", body: { bekraeft: true } }), "Demoen er nulstillet");
  state.requestIds = {};
  $("#chat").replaceChildren(h("p", { class: "empty" }, "Ingen spørgsmål endnu."));
  $("#plan-form [name=uge_start]").value = "";
  refresh();
});

// ---------------------------------------------------------------- Navigation og start
const LOADERS = { overview: loadOverview, plan: () => loadPlanTab(), stock: loadStock, ask: () => {}, data: loadData };

function refresh() {
  return Promise.allSettled([loadStatus(), LOADERS[state.tab]()]).then((results) => {
    const failed = results.find((r) => r.status === "rejected");
    if (failed) toast(failed.reason.message, "error");
  });
}

setupTabs((tab) => {
  state.tab = tab;
  refresh();
});

document.querySelectorAll("[data-goto]").forEach((button) => button.addEventListener("click", async () => {
  goTo(button.dataset.goto);
  if (button.dataset.scroll) setTimeout(() => $(`#${button.dataset.scroll}`).scrollIntoView({ behavior: "smooth" }), 300);
}));
document.querySelectorAll("[data-ask]").forEach((button) => button.addEventListener("click", () => {
  goTo("ask");
  ask(button.dataset.ask);
}));

$("#user-select").addEventListener("change", (event) => { state.userId = event.target.value; });

api("/users")
  .then((users) => {
    fillSelect($("#user-select"), users, (u) => `${u.navn} (${u.rolle})`);
    state.userId = $("#user-select").value;
    return refresh();
  })
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
