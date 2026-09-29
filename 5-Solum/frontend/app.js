// Solum – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { employeeId: null, employees: [], machines: [], machine: null, fault: null };

const LEVELS = ["under oplæring", "godkendt", "ekspert"];
const LEVEL_BADGE = { "under oplæring": "warn", godkendt: "ok", ekspert: "" };

function goTo(tab) {
  document.querySelector(`.tabs [data-tab="${tab}"]`).click();
}

// ---------------------------------------------------------------- Indlæsning
async function loadAll() {
  const [employees, machines] = await Promise.all([api("/employees"), api("/machines/overview")]);
  Object.assign(state, { employees, machines });
  if (!state.employeeId) {
    fillSelect($("#employee-select"), employees, (e) => e.name);
    state.employeeId = Number($("#employee-select").value);
  }
  renderMachines();
  loadArticles();
  loadMatrix();
  loadLog();
}

// ---------------------------------------------------------------- Startskærm: maskiner
function renderMachines() {
  $("#machine-grid").replaceChildren(...state.machines.map((m) =>
    h("button", { class: "machine-button", onclick: () => openMachine(m.id) },
      h("span", { class: "icon" }, m.icon),
      h("strong", {}, m.name),
      h("div", { class: "muted" }, `${m.location}${m.nickname ? ` · kaldes "${m.nickname}"` : ""}`),
      h("div", {}, badge(`${m.approved_operators} godkendte`, m.vulnerable ? "danger" : "ok"), " ",
        badge(`${m.articles} guides`), " ",
        m.faults_30d ? badge(`${m.faults_30d} fejl / 30 dage`, "warn") : ""))));
}

// ---------------------------------------------------------------- Maskineskærm
async function openMachine(machineId) {
  const details = await api(`/machines/${machineId}/details`);
  state.machine = details.machine;
  $("#guide-view").replaceChildren();

  const form = h("form", { class: "card highlight" },
    h("h2", {}, `${details.machine.icon} ${details.machine.name}`),
    h("label", {}, "Hvad er problemet?", h("input", { name: "symptom", required: true, placeholder: "fx stopper, nødstop, E-230", class: "big" })),
    h("div", { class: "actions" },
      h("button", { class: "big" }, "Find guide"),
      h("button", { type: "button", class: "big secondary", onclick: () => showGuideList(details.articles, null) }, "Vis kendte fejl")));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = await run(() => api("/faults", {
      method: "POST",
      body: { machine_id: machineId, employee_id: state.employeeId, symptom: form.elements.symptom.value },
    }));
    state.fault = result.fault;
    showGuideList(result.guides, result.experts);
    loadLog();
  });

  $("#machine-view").replaceChildren(
    form,
    h("div", { class: "grid wide" },
      h("div", { class: "card" },
        h("h3", {}, "Hyppige fejl på denne maskine"),
        details.fault_patterns.length
          ? h("ul", { class: "list" }, details.fault_patterns.map((p) =>
              h("li", {}, h("strong", {}, p.fault_type), ` – ${p.occurrences} gange, ca. ${p.avg_minutes ?? "?"} min. nedetid, ${p.solved} løst`)))
          : h("p", { class: "empty" }, "Ingen registrerede fejl")),
      h("div", { class: "card" },
        h("h3", {}, "Kolleger der kan hjælpe"),
        h("ul", { class: "list" }, details.experts.map((e) => h("li", {}, `${e.name} `, badge(e.level, LEVEL_BADGE[e.level])))))),
  );
  goTo("troubleshoot");
}

function showGuideList(guides, experts) {
  $("#guide-view").replaceChildren(h("div", { class: "card" },
    h("h2", {}, guides.length ? "Forslag til guides" : "Ingen guide fundet"),
    guides.length
      ? h("ul", { class: "list" }, guides.map((g) => h("li", {},
          h("button", { class: "secondary big", onclick: () => showGuide(g) }, g.title), " ",
          badge(g.level), " ",
          g.solve_rate !== null ? badge(`${Math.round(g.solve_rate * 100)} % løst`, g.solve_rate >= 0.7 ? "ok" : "warn") : "")))
      : h("p", {}, "Kontakt en erfaren kollega: ", (experts || []).map((e) => e.name).join(", ") || "–"),
  ));
}

function showGuide(guide) {
  const done = async (solved) => {
    if (!state.fault) {
      toast(solved ? "Godt klaret!" : "Kontakt en erfaren kollega");
      return;
    }
    const result = await run(() => api(`/faults/${state.fault.id}/resolve`, {
      method: "POST", body: { solved, article_id: guide.id },
    }), solved ? "Fejlen er logget som løst – tak!" : "Logget som uløst – kontakt en kollega");
    state.fault = null;
    $("#guide-view").append(solved
      ? h("div", { class: "card highlight" }, "✅ Maskinen kører igen. Din registrering forbedrer guiden.")
      : h("div", { class: "card", style: "border-color: var(--danger)" },
          h("strong", {}, "Kontakt en af disse kolleger: "),
          result.escalate_to.map((e) => `${e.name} (${e.level})`).join(", ") || "ingen registreret",
          h("p", { class: "muted" }, "Når fejlen er løst, kan kollegaen gemme løsningen under \"Bidrag med viden\".")));
    loadAll();
  };

  $("#guide-view").replaceChildren(h("div", { class: "card highlight" },
    h("p", {}, badge(guide.fault_type), " ", badge(guide.level), " ", h("span", { class: "muted" }, `Skrevet af ${guide.author_name}`)),
    h("h2", {}, guide.title),
    h("ol", { class: "steps" }, guide.steps.map((s) => h("li", {}, s))),
    guide.media_url ? h("p", {}, h("a", { href: guide.media_url, target: "_blank" }, "Se billede/video")) : "",
    h("div", { class: "actions" },
      h("button", { class: "big", onclick: () => done(true) }, "✅ Løst"),
      h("button", { class: "big danger", onclick: () => done(false) }, "Jeg har stadig problemer")),
  ));
}

// ---------------------------------------------------------------- Bidrag (CRUD for vidensartikler)
async function loadArticles() {
  const articles = await api("/articles");
  const form = $("#article-form");
  fillSelect(form.elements.machine_id, state.machines, (m) => `${m.icon} ${m.name}`);
  fillSelect(form.elements.author_id, state.employees, (e) => `${e.name}`);
  form.elements.author_id.value = state.employeeId;
  const machineName = Object.fromEntries(state.machines.map((m) => [m.id, m.name]));
  renderTable($("#article-table"), articles, [
    { label: "Maskine", render: (a) => machineName[a.machine_id] },
    { label: "Titel", key: "title" },
    { label: "Niveau", render: (a) => badge(a.level) },
    { label: "", render: (a) => crudButtons("articles", form, a, loadAll) },
  ]);
}

bindCrudForm($("#article-form"), "articles", loadAll);

// ---------------------------------------------------------------- Kompetenceoverblik
async function loadMatrix() {
  const { employees, machines, cells, approved_per_machine } = await api("/competence-matrix");
  $("#matrix").replaceChildren(h("div", { class: "table-wrap" }, h("table", { class: "matrix" },
    h("thead", {}, h("tr", {}, h("th", {}, "Medarbejder"), machines.map((m) =>
      h("th", { style: approved_per_machine[m.id] <= 1 ? "color: var(--danger)" : "" }, `${m.icon} ${m.name}`)))),
    h("tbody", {}, employees.map((e) => h("tr", {},
      h("th", {}, e.name),
      machines.map((m) => {
        const cell = cells[e.id]?.[m.id];
        return h("td", { onclick: () => cycleLevel(e.id, m.id, cell), title: "Klik for at ændre" },
          cell ? badge(cell.level, LEVEL_BADGE[cell.level]) : "–");
      })))),
    h("tfoot", {}, h("tr", {}, h("th", {}, "Godkendte"), machines.map((m) => h("td", {}, approved_per_machine[m.id])))),
  )));
}

async function cycleLevel(employeeId, machineId, cell) {
  const next = cell ? LEVELS[LEVELS.indexOf(cell.level) + 1] : LEVELS[0];
  if (!cell) {
    await run(() => api("/competences", { method: "POST", body: { employee_id: employeeId, machine_id: machineId, level: next } }), "Kompetence tilføjet");
  } else if (next) {
    await run(() => api(`/competences/${cell.id}`, { method: "PUT", body: { level: next } }), `Opdateret til ${next}`);
  } else {
    await run(() => api(`/competences/${cell.id}`, { method: "DELETE" }), "Kompetence fjernet");
  }
  loadAll();
}

// ---------------------------------------------------------------- Fejllog
async function loadLog() {
  const faults = await api("/faults");
  renderTable($("#fault-table"), faults, [
    { label: "Tid", render: (f) => formatDate(f.timestamp) },
    { label: "Maskine", key: "machine_name" },
    { label: "Medarbejder", key: "employee_name" },
    { label: "Symptom", key: "symptom" },
    { label: "Guide", key: "article_title" },
    { label: "Min.", class: "num", key: "duration_minutes" },
    { label: "Status", render: (f) => badge(f.status, { LØST: "ok", ULØST: "danger", ÅBEN: "warn" }[f.status]) },
  ]);
}

// ---------------------------------------------------------------- Start
$("#employee-select").addEventListener("change", (event) => {
  state.employeeId = Number(event.target.value);
  $("#article-form").elements.author_id.value = state.employeeId;
});

setupTabs();
loadAll().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
