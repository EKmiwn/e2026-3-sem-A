// Learnify – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { role: null, user: null, classes: [] };

const CATEGORIES = ["trivsel", "læring", "møbler", "miljø"];
const SMILEYS = [["😞", "Slet ikke"], ["🙁", "Lidt"], ["😐", "Nogenlunde"], ["🙂", "Meget"], ["😄", "Helt enig"]];

function bar(pct) {
  return h("div", { class: "bar", title: `${pct ?? 0} %` }, h("span", { style: `width:${pct ?? 0}%` }));
}

function avgBadge(value) {
  if (value === null || value === undefined) return "–";
  return badge(value.toFixed(1), value >= 3.5 ? "ok" : value >= 2.75 ? "warn" : "danger");
}

// ---------------------------------------------------------------- Login og roller
$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { role, user } = await run(() => api("/login", { method: "POST", body: formToJson(event.target) }));
  Object.assign(state, { role, user });
  $("#login").hidden = true;
  $("#tabs").hidden = false;
  $("#who").replaceChildren(`${user.name} (${role}${user.class_name ? `, ${user.class_name}` : ""}) `,
    h("button", { class: "small secondary", onclick: () => location.reload() }, "Log ud"));

  const buttons = [...document.querySelectorAll("#tabs button")];
  buttons.forEach((b) => (b.hidden = !b.dataset.role.split(" ").includes(role)));
  buttons.find((b) => !b.hidden).click();

  if (role === "elev") loadStudent();
  else loadTeacher();
});

// ---------------------------------------------------------------- Elev: besvar og følg egen udvikling
async function loadStudent() {
  const survey = await api(`/survey?student_id=${state.user.id}`);
  $("#period").textContent = `(uge ${survey.period.slice(-2)})`;
  const form = $("#survey-form");
  if (survey.already_answered) {
    form.replaceChildren(h("p", { class: "empty" }, "Du har allerede svaret i denne uge. Tak! Se din udvikling under \"Min udvikling\"."));
  } else {
    form.replaceChildren(
      ...survey.questions.map((q) => h("fieldset", {},
        h("legend", {}, q.text, " ", badge(q.category, "muted")),
        h("div", { class: "scale" }, SMILEYS.map(([icon, text], i) =>
          h("label", {}, h("input", { type: "radio", name: `q${q.id}`, value: i + 1, required: true }), icon, h("small", {}, text)))))),
      h("label", {}, "Vil du fortælle mere? (valgfrit)", h("textarea", { name: "comment" })),
      h("button", {}, "Send mine svar"),
    );
    form.onsubmit = (event) => submitSurvey(event, survey.questions);
  }
  loadHistory();
}

async function submitSurvey(event, questions) {
  event.preventDefault();
  const form = event.target;
  const answers = questions.map((q) => ({ question_id: q.id, value: Number(form.elements[`q${q.id}`].value) }));
  const result = await run(() => api("/responses", {
    method: "POST", body: { student_id: state.user.id, answers, comment: form.elements.comment.value },
  }), "Tak for dine svar!");
  form.replaceChildren();
  $("#survey-result").replaceChildren(h("div", { class: "card highlight" },
    h("p", {}, result.feedback),
    h("p", {}, h("strong", {}, "Forslag til dig: "), result.suggestion),
    h("p", {}, Object.entries(result.your_averages).map(([c, v]) => [badge(`${c}: ${v}`), " "]))));
  loadHistory();
}

async function loadHistory() {
  const history = await api(`/students/${state.user.id}/history`);
  renderTable($("#history-table"), CATEGORIES.map((c) => ({ category: c, values: history.categories[c] })), [
    { label: "Kategori", key: "category" },
    ...history.periods.map((p, i) => ({ label: `Uge ${p.slice(-2)}`, render: (row) => avgBadge(row.values[i]) })),
  ], "Du har ikke svaret endnu");
}

// ---------------------------------------------------------------- Lærer: resultater og udvikling
async function loadTeacher() {
  state.classes = await api("/classes");
  for (const select of [$("#results-form [name=class_id]"), $("#trend-form [name=class_id]")]) {
    fillSelect(select, state.classes, (c) => c.name, { placeholder: "Hele skolen" });
    select.value = state.classes[0]?.id ?? "";
  }
  await loadResults();
  loadTrend();
  if (state.role === "administrator") {
    loadOverview();
    loadManage();
  }
}

async function loadResults(keepPeriod = false) {
  const form = $("#results-form");
  const params = new URLSearchParams(formToJson(form));
  if (!keepPeriod) params.delete("period");
  const r = await api(`/results?${params}`);
  fillSelect(form.elements.period, [...r.periods].reverse().map((p) => ({ id: p })), (p) => `Uge ${p.id.slice(-2)} (${p.id})`);
  form.elements.period.value = r.period ?? "";

  if (r.hidden) {
    $("#result-kpis").replaceChildren(h("p", { class: "empty" }, r.message));
    $("#result-table").replaceChildren();
    $("#comment-list").replaceChildren();
    return;
  }
  $("#result-kpis").replaceChildren(
    kpi(r.respondents, "elever har svaret"),
    kpi(`${r.overall.positive_pct} %`, "positive svar (4–5)"),
    ...CATEGORIES.map((c) => kpi(r.categories[c].average?.toFixed(1) ?? "–", `${c} · ${r.categories[c].positive_pct ?? 0} % positive`)),
  );
  renderTable($("#result-table"), r.questions, [
    { label: "Spørgsmål", key: "text" },
    { label: "Kategori", render: (q) => badge(q.category, "muted") },
    { label: "Gns.", render: (q) => avgBadge(q.average) },
    { label: "Positive", render: (q) => h("div", {}, bar(q.positive_pct), `${q.positive_pct ?? 0} %`) },
    { label: "Negative", class: "num", render: (q) => `${q.negative_pct ?? 0} %` },
  ]);
  $("#comment-list").replaceChildren(...(r.comments.length
    ? r.comments.map((c) => h("li", {}, `"${c}"`))
    : [h("li", { class: "empty" }, "Ingen kommentarer")]));
}

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value), h("div", { class: "label" }, label));
}

$("#results-form [name=class_id]").addEventListener("change", () => loadResults(false));
$("#results-form [name=period]").addEventListener("change", () => loadResults(true));

async function loadTrend() {
  const params = new URLSearchParams(formToJson($("#trend-form")));
  const t = await api(`/results/trend?${params}`);
  renderTable($("#trend-table"), CATEGORIES.map((c) => ({ category: c, series: t.series[c], change: t.change_since_first[c] })), [
    { label: "Kategori", key: "category" },
    ...t.periods.map((p, i) => ({
      label: `Uge ${p.slice(-2)}`,
      render: (row) => h("div", {}, avgBadge(row.series[i].average), h("div", { class: "muted" }, `${row.series[i].positive_pct} %`)),
    })),
    { label: "Ændring", render: (row) => row.change === null ? "–" : badge(`${row.change > 0 ? "+" : ""}${row.change}`, row.change >= 0 ? "ok" : "danger") },
  ]);
}

$("#trend-form").addEventListener("change", loadTrend);

// ---------------------------------------------------------------- Administrator
async function loadOverview() {
  const classes = await api("/overview");
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
    { label: "Kategori", key: "category" },
    { label: "Aktiv", render: (q) => (q.active ? "Ja" : "Nej") },
    { label: "", render: (q) => crudButtons("questions", $("#question-form"), q, loadManage) },
  ]);
  fillSelect($("#student-form [name=class_id]"), state.classes, (c) => c.name);
  renderTable($("#student-table"), students, [
    { label: "Navn", key: "name" },
    { label: "Brugernavn", key: "username" },
    { label: "Klasse", render: (s) => className[s.class_id] },
    { label: "", render: (s) => crudButtons("students", $("#student-form"), s, loadManage) },
  ]);
}

bindCrudForm($("#question-form"), "questions", loadManage);
bindCrudForm($("#student-form"), "students", loadManage);

// ---------------------------------------------------------------- Start
setupTabs();
api("/health").catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
