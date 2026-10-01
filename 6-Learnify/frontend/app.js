// Learnify – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { role: null, user: null, classes: [] };

const CATEGORIES = ["trivsel", "læring", "møbler", "miljø"];
const SMILEYS = [["😞", "Slet ikke"], ["🙁", "Lidt"], ["😐", "Nogenlunde"], ["🙂", "Meget"], ["😄", "Helt enig"]];
const MONTHS = ["januar", "februar", "marts", "april", "maj", "juni", "juli", "august", "september", "oktober", "november", "december"];

// Den indloggede bruger sendes med som "rolle:id" (simuleret session)
function userApi(path, options = {}) {
  return api(path, { ...options, headers: { "X-User-Id": `${state.role}:${state.user.id}` } });
}

function monthName(period) {
  const [year, month] = period.split("-");
  return `${MONTHS[Number(month) - 1]} ${year}`;
}

function pct(value) {
  if (value === null || value === undefined) return h("span", { class: "muted" }, "–");
  return h("span", { class: `pct ${value >= 60 ? "hi" : value >= 35 ? "mid" : "lo"}` }, `${value} %`);
}

function avgBadge(value) {
  if (value === null || value === undefined) return "–";
  return badge(value.toFixed(1), value >= 3.5 ? "ok" : value >= 2.75 ? "warn" : "danger");
}

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value ?? "–"), h("div", { class: "label" }, label));
}

// ---------------------------------------------------------------- Login: vælg elev, lærer eller virksomhed
document.querySelectorAll("#role-buttons button").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll("#role-buttons button").forEach((b) => b.classList.toggle("active", b === button));
  $("#login-form").elements.role.value = button.dataset.role;
}));

$("#forgot").addEventListener("click", (event) => {
  event.preventDefault();
  toast("Kontakt din lærer eller skolens administrator for at få en ny adgangskode.");
});

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { role, user } = await run(() => api("/login", { method: "POST", body: formToJson(event.target) }));
  Object.assign(state, { role, user });
  $("#login-screen").hidden = true;
  $("#app").hidden = false;
  $("#who").replaceChildren(h("span", {}, `${user.name}${user.class_name ? ` · ${user.class_name}` : ""} · ${role}`),
    h("button", { class: "small secondary", onclick: () => location.reload() }, "Log ud"));
  const buttons = [...document.querySelectorAll("#tabs button")];
  buttons.forEach((b) => (b.hidden = !b.dataset.role.split(" ").includes(role)));
  if (role !== "elev") state.classes = await api("/classes");
  buttons.find((b) => !b.hidden).click();       // elev → forsiden, lærer → elevernes besvarelser
});

// ---------------------------------------------------------------- Elev: forside med personlig profil
async function loadHome() {
  const p = await userApi("/me/profile");
  $("#my-profile").replaceChildren(
    p.answered_this_month ? null : h("div", { class: "card highlight" },
      h("h2", {}, `Månedens test for ${monthName(new Date().toISOString().slice(0, 7))} er klar`),
      h("p", {}, "Det tager ca. 5 minutter. Dine svar hjælper din lærer med at gøre klassen bedre for dig."),
      h("button", { onclick: () => document.querySelector('#tabs button[data-tab="survey"]').click() }, "Tag testen nu")),
    profileView(p));
}

function profileView(p) {
  const s = p.student;
  return h("div", {},
    h("div", { class: "profile" },
      h("div", { class: "card" },
        h("div", { class: "actions", style: "align-items:center;margin-bottom:12px" },
          h("div", { class: "avatar" }, s.name.split(" ").map((n) => n[0]).join("")),
          h("div", {}, h("h2", { style: "margin:0" }, s.name), h("span", { class: "muted" }, `Klasse ${s.class_name}`))),
        h("dl", {},
          h("dt", {}, "Elev"), h("dd", {}, s.name),
          h("dt", {}, "Klasse"), h("dd", {}, s.class_name),
          h("dt", {}, "Alder"), h("dd", {}, s.age ? `${s.age} år` : "–"),
          h("dt", {}, "Læringsstil"), h("dd", {}, p.learning_style ?? "–"),
          h("dt", {}, "Arbejdstempo"), h("dd", {}, p.work_pace ?? "–"))),
      h("div", { class: "card" },
        h("div", { class: "grid" },
          h("div", {}, h("div", { class: "muted" }, "Seneste trivselsscore"),
            h("div", { class: "score" }, p.wellbeing_score ?? "–", h("small", {}, "/10"))),
          h("div", {}, h("div", { class: "muted" }, "Klasselokale og indretning"),
            h("div", { class: "score" }, p.classroom_score ?? "–", h("small", {}, "/10")))),
        h("h3", {}, "Forbedringer eleven ønsker"), h("p", {}, p.wishes ?? h("span", { class: "muted" }, "Ingen ønsker skrevet")),
        h("h3", {}, "Holdning til klasselokalet og indretningen"), h("p", {}, p.classroom ?? h("span", { class: "muted" }, "Intet skrevet")),
        p.comment ? h("p", { class: "muted" }, `"${p.comment}"`) : null)),
    h("div", { class: "card" },
      h("h3", {}, "Svar pr. måned (andel positive svar)"),
      chart(p.months),
      monthTable(p.months)),
    p.notes.length ? h("div", { class: "card" }, h("h3", {}, `Uddybninger (${monthName(p.latest_period)})`),
      h("ul", { class: "list" }, p.notes.map((n) => h("li", {}, badge(n.category, "muted"), ` ${n.question}: `,
        h("strong", {}, SMILEYS[n.value - 1][0]), h("br"), h("em", {}, `"${n.note}"`))))) : null);
}

// Diagram: søjler pr. kategori for hver måned
function chart(months) {
  if (!months.length) return h("p", { class: "empty" }, "Ingen besvarelser endnu");
  return h("div", {},
    h("div", { class: "chart" }, months.map((m) => h("div", { class: "month" },
      h("div", { class: "bars" }, CATEGORIES.map((c) => h("span", {
        class: `c-${c}`, title: `${c}: ${m.categories[c].positive_pct ?? 0} %`, style: `height:${m.categories[c].positive_pct ?? 0}%`,
      }))),
      h("small", {}, monthName(m.period))))),
    h("div", { class: "legend" }, CATEGORIES.map((c) => h("span", {}, h("i", { class: `c-${c}` }), c))));
}

function monthTable(months) {
  const box = h("div");
  renderTable(box, CATEGORIES.map((c) => ({ category: c })), [
    { label: "Kategori", key: "category" },
    ...months.map((m) => ({ label: monthName(m.period), render: (row) => pct(m.categories[row.category].positive_pct) })),
  ]);
  return box;
}

// ---------------------------------------------------------------- Elev: månedens test
async function loadSurvey() {
  const survey = await userApi("/survey");
  $("#period").textContent = `(${monthName(survey.period)})`;
  const form = $("#survey-form");
  $("#survey-result").replaceChildren();
  if (survey.already_answered) {
    form.replaceChildren(h("p", { class: "empty" }, "Du har allerede taget månedens test. Tak! Se din profil på forsiden."));
    return;
  }
  const question = (q) => h("fieldset", { class: "question" },
    h("legend", {}, q.text),
    h("div", { class: "scale" }, SMILEYS.map(([icon, text], i) =>
      h("label", {}, h("input", { type: "radio", name: `q${q.id}`, value: i + 1, required: true }), icon, h("small", {}, text)))),
    h("input", { name: `note${q.id}`, placeholder: "Uddyb (valgfrit) – fx hvorfor?", maxlength: 500 }));
  const sections = [["trivsel", "Trivsel"], ["læring", "Læring"], ["møbler", "Møbler"], ["miljø", "Miljø og larm"],
    ["arbejdsstil", "Din arbejdsstil – så din lærer kan støtte dig bedst"]];
  form.replaceChildren(
    ...sections.flatMap(([cat, title]) => {
      const qs = survey.questions.filter((q) => q.category === cat);
      return qs.length ? [h("h3", { class: "section-title" }, title), ...qs.map(question)] : [];
    }),
    h("h3", { class: "section-title" }, "Med dine egne ord"),
    h("label", {}, "Hvilke forbedringer ønsker du?", h("textarea", { name: "wishes", maxlength: 500 })),
    h("label", {}, "Hvad synes du om klasselokalet og indretningen?", h("textarea", { name: "classroom", maxlength: 500 })),
    h("label", {}, "Er der andet, du vil fortælle? (valgfrit)", h("textarea", { name: "comment", maxlength: 500 })),
    h("button", {}, "Send mine svar"));
  form.onsubmit = (event) => submitSurvey(event, survey.questions);
}

async function submitSurvey(event, questions) {
  event.preventDefault();
  const form = event.target;
  const answers = questions.map((q) => ({
    question_id: q.id, value: Number(form.elements[`q${q.id}`].value), note: form.elements[`note${q.id}`].value,
  }));
  const result = await run(() => userApi("/responses", {
    method: "POST",
    body: { answers, wishes: form.elements.wishes.value, classroom: form.elements.classroom.value, comment: form.elements.comment.value },
  }), "Tak for dine svar!");
  form.replaceChildren();
  $("#survey-result").replaceChildren(h("div", { class: "card highlight" },
    h("p", {}, result.feedback),
    h("p", {}, h("strong", {}, "Forslag til dig: "), result.suggestion),
    h("p", {}, `Din trivselsscore: ${result.profile.wellbeing_score}/10 · Læringsstil: ${result.profile.learning_style ?? "–"}`)));
}

// ---------------------------------------------------------------- Lærer: hver elev i procent pr. måned
async function loadStudents() {
  const t = await userApi("/teacher/students");
  $("#teacher-class").textContent = t.class_id ? `· ${state.classes.find((c) => c.id === t.class_id)?.name}` : "· alle klasser";
  renderTable($("#student-table"), t.students, [
    { label: "Navn", render: (s) => h("strong", {}, s.name) },
    { label: "Klasse", key: "class_name" },
    { label: "Trivsel", class: "num", render: (s) => (s.wellbeing_score ? `${s.wellbeing_score}/10` : "–") },
    { label: "Læringsstil", key: "learning_style" },
    { label: "Tempo", key: "work_pace" },
    ...t.periods.map((p) => ({
      label: monthName(p),
      render: (s) => (s.months[p] ? h("span", { title: CATEGORIES.map((c) => `${c}: ${s.months[p][c]} %`).join(" · ") }, pct(s.months[p].samlet)) : pct(null)),
    })),
  ], "Ingen elever");
  $("#student-table").querySelectorAll("tbody tr").forEach((tr, i) => {
    tr.classList.add("clickable");
    tr.addEventListener("click", () => openStudent(t.students[i].id));
  });
}

async function openStudent(id) {
  const p = await userApi(`/students/${id}/profile`);
  $("#student-profile").replaceChildren(profileView(p));
  $("#student-profile").scrollIntoView({ behavior: "smooth" });
}

async function loadResults(keepPeriod = false) {
  const form = $("#results-form");
  const params = new URLSearchParams(keepPeriod ? formToJson(form) : {});
  const r = await userApi(`/results?${params}`);
  fillSelect(form.elements.period, [...r.periods].reverse().map((p) => ({ id: p })), (p) => monthName(p.id));
  form.elements.period.value = r.period ?? "";
  if (r.hidden) {
    $("#result-kpis").replaceChildren(h("p", { class: "empty" }, r.message));
    $("#result-table").replaceChildren();
    return;
  }
  $("#result-kpis").replaceChildren(
    kpi(r.respondents, "elever har svaret"),
    kpi(`${r.overall.positive_pct} %`, "positive svar (4–5)"),
    ...CATEGORIES.map((c) => kpi(r.categories[c].average?.toFixed(1) ?? "–", `${c} · ${r.categories[c].positive_pct ?? 0} % positive`)));
  renderTable($("#result-table"), r.questions, [
    { label: "Spørgsmål", key: "text" },
    { label: "Kategori", render: (q) => badge(q.category, "muted") },
    { label: "Gns.", render: (q) => avgBadge(q.average) },
    { label: "Positive", render: (q) => pct(q.positive_pct) },
    { label: "Negative", class: "num", render: (q) => `${q.negative_pct ?? 0} %` },
  ]);
}

$("#results-form [name=period]").addEventListener("change", () => loadResults(true));

async function loadTrend() {
  const form = $("#trend-form");
  if (!form.elements.class_id.options.length) {
    fillSelect(form.elements.class_id, state.role === "lærer" && state.user.class_id
      ? state.classes.filter((c) => c.id === state.user.class_id) : state.classes, (c) => c.name, { placeholder: "Alle klasser" });
  }
  const t = await userApi(`/results/trend?${new URLSearchParams(formToJson(form))}`);
  renderTable($("#trend-table"), CATEGORIES.map((c) => ({ category: c, series: t.series[c], change: t.change_since_first[c] })), [
    { label: "Kategori", key: "category" },
    ...t.periods.map((p, i) => ({
      label: monthName(p),
      render: (row) => h("div", {}, avgBadge(row.series[i].average), h("div", { class: "muted" }, `${row.series[i].positive_pct} %`)),
    })),
    { label: "Ændring", render: (row) => (row.change === null ? "–" : badge(`${row.change > 0 ? "+" : ""}${row.change}`, row.change >= 0 ? "ok" : "danger")) },
  ]);
}

$("#trend-form").addEventListener("change", loadTrend);

// ---------------------------------------------------------------- Virksomhed: filtrerede besvarelser
async function loadCompany() {
  const form = $("#company-form");
  const first = !form.elements.class_id.options.length;
  if (first) fillSelect(form.elements.class_id, state.classes, (c) => c.name, { placeholder: "Alle" });
  const filters = Object.fromEntries(Object.entries(formToJson(form)).filter(([, v]) => v !== "" && v !== false).map(([k, v]) => [k, v === true ? 1 : v]));
  const c = await userApi(`/company/answers?${new URLSearchParams(filters)}`);
  if (first) {
    fillSelect(form.elements.period, c.filters.periods.map((p) => ({ id: p })), (p) => monthName(p.id), { placeholder: "Alle" });
    fillSelect(form.elements.category, c.filters.categories.map((k) => ({ id: k })), (k) => k.id, { placeholder: "Alle" });
  }
  $("#company-kpis").replaceChildren(
    kpi(c.count, "svar matcher filteret"),
    kpi(c.summary.average?.toFixed(1), "gennemsnit (1–5)"),
    kpi(c.summary.positive_pct !== null ? `${c.summary.positive_pct} %` : "–", "positive svar"),
    ...CATEGORIES.filter((k) => c.per_category[k].answers).map((k) => kpi(`${c.per_category[k].positive_pct} %`, `${k} positive`)));
  renderTable($("#company-table"), c.answers, [
    { label: "Elev", key: "student" },
    { label: "Måned", render: (a) => monthName(a.period) },
    { label: "Spørgsmål", render: (a) => h("span", {}, a.question, a.note ? h("br") : null, a.note ? h("em", { class: "muted" }, `"${a.note}"`) : null) },
    { label: "Svar", render: (a) => h("span", { title: `${a.value}/5` }, SMILEYS[a.value - 1][0]) },
  ], "Ingen besvarelser matcher filteret");
  $("#company-wishes").replaceChildren(...(c.wishes.length ? c.wishes.map((w) => h("li", {},
    h("small", { class: "muted" }, `${w.class_name} · ${monthName(w.period)}`),
    w.wishes ? h("div", {}, "💡 ", w.wishes) : null, w.classroom ? h("div", {}, "🏫 ", w.classroom) : null))
    : [h("li", { class: "empty" }, "Ingen")]));
}

$("#company-form").addEventListener("change", loadCompany);

async function loadOverview() {
  const classes = await userApi("/overview");
  renderTable($("#overview-table"), classes, [
    { label: "Klasse", key: "name" },
    { label: "Elever", class: "num", key: "students" },
    ...CATEGORIES.map((c) => ({
      label: c,
      render: (row) => h("span", {}, avgBadge(row.latest[c]), h("span", { class: "muted" }, ` (fra ${row.first[c]?.toFixed(1) ?? "–"})`)),
    })),
  ]);
}

async function loadManage() {
  const [questions, students] = await Promise.all([api("/questions"), api("/students")]);
  const className = Object.fromEntries(state.classes.map((c) => [c.id, c.name]));
  renderTable($("#question-table"), questions, [
    { label: "Spørgsmål", key: "text" },
    { label: "Kategori", render: (q) => `${q.category}${q.style ? ` (${q.style})` : ""}` },
    { label: "Aktiv", render: (q) => (q.active ? "Ja" : "Nej") },
    { label: "", render: (q) => crudButtons("questions", $("#question-form"), q, loadManage) },
  ]);
  fillSelect($("#student-form [name=class_id]"), state.classes, (c) => c.name);
  renderTable($("#manage-student-table"), students, [
    { label: "Navn", key: "name" },
    { label: "E-mail", key: "email" },
    { label: "Klasse", render: (s) => className[s.class_id] },
    { label: "", render: (s) => crudButtons("students", $("#student-form"), s, loadManage) },
  ]);
}

bindCrudForm($("#question-form"), "questions", loadManage);
bindCrudForm($("#student-form"), "students", loadManage);

// ---------------------------------------------------------------- Start
setupTabs((tab) => {
  ({ home: loadHome, survey: loadSurvey, students: loadStudents, results: loadResults, trend: loadTrend,
    company: loadCompany, overview: loadOverview, manage: loadManage })[tab]?.();
});
api("/health").catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
