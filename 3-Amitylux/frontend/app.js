// Amitylux Experience Compass – presentation layer. All matching happens in the API (compass.py).

const STEPS = ["start", "preferences", "summary", "results", "compare", "request"];
const NEXT_LABEL = { start: "Start", preferences: "Check my answers", summary: "Show my suggestions",
  results: "Compare types", compare: "Continue to request" };
const STATUS_BADGE = { NEW: "warn", IN_PROGRESS: "", ANSWERED: "ok", CLOSED: "muted" };

const state = {
  step: "start",
  options: null, destinations: [], types: [], addons: [], claims: [],
  prefs: { group_size: 2, interests: [], practical: [], language: "English", pace: "moderate" },
  result: null,          // latest /compass response – its .preferences are the "before" of the next change (K3)
  chosen: new Set(),     // experience ids the customer keeps
  wantedType: null,
  chosenAddons: [],
};

// ---------------------------------------------------------------- Helpers
function radioChips(container, name, entries, selected, onChange, type = "radio") {
  const legend = container.querySelector("legend");
  container.replaceChildren(legend, ...entries.map(([value, label]) =>
    h("label", {},
      h("input", { type, name, value, checked: type === "radio" ? String(selected) === String(value) : selected.includes(value),
        onchange: (e) => onChange(value, e.target.checked) }),
      h("span", {}, label))));
}

function toggle(list, value, on) {
  return on ? [...new Set([...list, value])] : list.filter((v) => v !== value);
}

function showErrors(errors = {}) {
  document.querySelectorAll("[data-error]").forEach((p) => (p.textContent = errors[p.dataset.error] || ""));
}

function label(dict, key) { return dict?.[key] ?? key; }

// ---------------------------------------------------------------- K10 Stepper: progress, active choices, back
function goTo(step) {
  state.step = step;
  const index = STEPS.indexOf(step);
  STEPS.forEach((s) => $(`#step-${s}`).classList.toggle("active", s === step));
  $("#progress").replaceChildren(...STEPS.map((_, i) => h("span", { class: i <= index ? "done" : "" })));
  $("#step-label").textContent = `Step ${index + 1} of ${STEPS.length} · ${$(`#step-${step}`).dataset.title}`;
  $("#back-button").hidden = index === 0;
  $("#next-button").hidden = !NEXT_LABEL[step];
  $("#next-button").textContent = NEXT_LABEL[step] || "";
  showErrors();
  renderActiveChoices();
  if (step === "summary") renderSummary();
  if (step === "compare") renderCompare();
  if (step === "request") renderRequest();
  window.scrollTo({ top: 0 });
}

function renderActiveChoices() {
  const p = state.prefs, o = state.options;
  const destination = state.destinations.find((d) => d.id === p.destination_id);
  const chips = [
    destination?.name,
    p.group_type && `${p.group_size} · ${label(o.group_types, p.group_type)}`,
    ...p.interests.map((i) => label(o.interests, i)),
    STEPS.indexOf(state.step) > 1 && p.pace && `${label(o.paces, p.pace)} pace`,
    STEPS.indexOf(state.step) > 1 && p.language,
    ...p.practical.map((x) => label(o.practical, x)),
  ].filter(Boolean);
  $("#active-choices").replaceChildren(...chips.map((c) => badge(c)));
}

$("#back-button").addEventListener("click", () => goTo(STEPS[Math.max(STEPS.indexOf(state.step) - 1, 0)]));

$("#next-button").addEventListener("click", async () => {
  const step = state.step;
  if (step === "start") {
    if (!state.prefs.destination_id) return showErrors({ destination_id: "Choose a destination" });
    return goTo("preferences");
  }
  if (step === "preferences") {
    const errors = localErrors();
    if (Object.keys(errors).length) return showErrors(errors);
    return goTo("summary");
  }
  if (step === "summary") {
    await fetchSuggestions();
    return goTo("results");
  }
  if (step === "results") return goTo("compare");
  if (step === "compare") {
    if (!state.wantedType) return showErrors({ wanted_type: "Choose a type – or talk to a person" });
    return goTo("request");
  }
});

// Same rules as compass.validate() – the API checks again
function localErrors() {
  const p = state.prefs, errors = {};
  if (!p.group_type) errors.group_type = "Choose who is travelling";
  if (!(p.group_size >= 1 && p.group_size <= 40)) errors.group_size = "Group size must be between 1 and 40";
  if (!p.interests.length) errors.interests = "Choose at least one interest";
  if (!p.pace) errors.pace = "Choose a pace";
  return errors;
}

// ---------------------------------------------------------------- Step 1–2: K1 preferences
function renderPreferenceInputs() {
  const o = state.options, p = state.prefs;
  const set = (key) => (value) => { p[key] = value; renderActiveChoices(); };
  radioChips($("#destination-choices"), "destination", state.destinations.map((d) => [d.id, `${d.name}, ${d.country}`]),
    p.destination_id, (v) => { p.destination_id = Number(v); renderActiveChoices(); });
  radioChips($("#group-type-choices"), "group_type", Object.entries(o.group_types), p.group_type, set("group_type"));
  radioChips($("#pace-choices"), "pace", Object.entries(o.paces), p.pace, set("pace"));
  radioChips($("#interest-choices"), "interests", Object.entries(o.interests), p.interests,
    (v, on) => { p.interests = toggle(p.interests, v, on); renderActiveChoices(); }, "checkbox");
  radioChips($("#practical-choices"), "practical", Object.entries(o.practical), p.practical,
    (v, on) => { p.practical = toggle(p.practical, v, on); renderActiveChoices(); }, "checkbox");
  for (const select of [$("#language-select"), $("#adjust-language")])
    select.replaceChildren(...o.languages.map((l) => h("option", { selected: l === p.language }, l)));
  $("#adjust-pace").replaceChildren(...Object.entries(o.paces).map(([v, l]) => h("option", { value: v, selected: v === p.pace }, l)));
  $("#prefs-form [name=group_size]").value = p.group_size;
  $("#adjust-form [name=group_size]").value = p.group_size;
}

$("#prefs-form").addEventListener("input", (e) => {
  const { name, value } = e.target;
  if (name === "group_size") state.prefs.group_size = Number(value);
  if (name === "language") state.prefs.language = value;
  if (name === "travel_date") state.prefs.travel_date = value || undefined;
  renderActiveChoices();
});

// ---------------------------------------------------------------- Step 3: summary
function renderSummary() {
  const p = state.prefs, o = state.options;
  const rows = [
    ["Destination", state.destinations.find((d) => d.id === p.destination_id)?.name, "start"],
    ["Who", `${p.group_size} · ${label(o.group_types, p.group_type)}`, "preferences"],
    ["Interests", p.interests.map((i) => label(o.interests, i)).join(", "), "preferences"],
    ["Pace", label(o.paces, p.pace), "preferences"],
    ["Guide language", p.language, "preferences"],
    ["Practical", p.practical.map((x) => label(o.practical, x)).join(", ") || "None", "preferences"],
    ["Travel date", p.travel_date || "Not given", "preferences"],
  ];
  renderTable($("#prefs-summary"), rows.map(([field, value, step]) => ({ field, value, step })), [
    { label: "Question", render: (r) => h("strong", {}, r.field) },
    { label: "Your answer", key: "value" },
    { label: "", render: (r) => h("button", { class: "small secondary", type: "button", onclick: () => goTo(r.step) }, "Change") },
  ]);
}

// ---------------------------------------------------------------- Step 4: K2, K3 suggestions
// After the first result, every new call sends the previous answers along, so the API can say what changed
async function fetchSuggestions() {
  const previous = state.result?.preferences;
  const body = { preferences: state.prefs, ...(previous ? { previous } : {}) };
  try {
    state.result = await api("/compass", { method: "POST", body });
  } catch (err) {
    toast(err.message, "error");
    throw err;
  }
  const shown = new Set(state.result.suggestions.map((s) => s.experience.id));
  state.chosen = new Set([...state.chosen].filter((id) => shown.has(id)));
  renderResults();
}

function renderResults() {
  const r = state.result;
  $("#adjust-form [name=group_size]").value = state.prefs.group_size;
  $("#adjust-pace").value = state.prefs.pace;
  $("#adjust-language").value = state.prefs.language;
  renderChanges(r.changes);
  const added = new Set(r.changes?.added || []);
  const changedReasons = new Set(r.changes?.reasons_changed || []);
  $("#results").replaceChildren(
    h("p", { class: "muted" },
      `We checked ${r.checked.approved_in_destination} approved Amitylux experiences in ${r.destination.name}. `,
      `${r.checked.matching} fit your group, language and interests – here are the ${r.checked.shown} that fit best.`),
    r.suggestions.length
      ? h("div", { class: "grid" }, r.suggestions.map((s) => suggestionCard(s, added.has(s.experience.title), changedReasons.has(s.experience.title))))
      : h("div", { class: "card" }, h("p", {}, "No experience in the catalogue fits all your answers."),
          h("p", { class: "muted" }, "Try changing one answer – or talk to a person, who can put something together for you."),
          h("button", { onclick: () => $("#help-button").click() }, "Talk to a person")),
  );
  renderWhyAmitylux();
}

// K5 all fields · K3 reasons · K6 local note · K7 value · K9 requires confirmation · K12 mobility
function suggestionCard(s, isNew, reasonsChanged) {
  const e = s.experience;
  const kept = state.chosen.has(e.id);
  return h("article", { class: `card suggestion slot-${s.slot}` },
    h("p", {}, badge(s.slot_label), " ", badge(e.type_name, "muted"), " ",
      isNew ? badge("New after your change", "new-tag") : "", reasonsChanged ? badge("Reasons updated", "ok") : ""),
    h("p", { class: "muted", style: "margin:0" }, s.slot_hint),
    h("h3", {}, e.title),
    h("p", {}, e.description),
    h("div", { class: "why" },
      h("strong", {}, "Why this fits you"),
      h("ul", {}, s.reasons.map((r) => h("li", {}, r.text))),
      s.cautions.length ? h("p", { class: "muted", style: "margin:4px 0 0" }, "Note: ", s.cautions.join(" ")) : ""),
    e.local_alternative && e.local_note ? h("p", {}, h("strong", {}, "Local choice: "), e.local_note) : "",
    h("dl", { class: "facts" },
      h("dt", {}, "Where"), h("dd", {}, e.location),
      h("dt", {}, "Type"), h("dd", {}, e.experience_type),
      h("dt", {}, "Duration"), h("dd", {}, `${e.duration_hours} hours`),
      h("dt", {}, "Group"), h("dd", {}, `${e.type_name} · ${e.group}`),
      h("dt", {}, "Getting around"), h("dd", {}, e.transport.join(", "), e.mobility_note ? h("div", { class: "muted" }, e.mobility_note) : ""),
      h("dt", {}, "Languages"), h("dd", {}, e.languages.join(", ")),
      h("dt", {}, "Included"), h("dd", {}, e.included),
      h("dt", {}, "Not included"), h("dd", {}, e.not_included),
      h("dt", {}, "Price"), h("dd", {}, h("strong", {}, e.price_label), h("span", { class: "muted" }, " · catalogue price")),
    ),
    s.requires_confirmation.length ? h("div", { class: "confirm" },
      badge("requires confirmation", "warn"), " Not confirmed yet – a person checks:",
      h("ul", {}, s.requires_confirmation.map((c) => h("li", {}, c)))) : "",
    s.amitylux_value.length ? h("p", {}, s.amitylux_value.map((v) => [h("span", { class: "badge ok", title: v.text }, v.label), " "])) : "",
    e.rating ? h("p", { style: "font-size:0.9rem" }, `★ ${e.rating} (${e.review_count} reviews) `, h("em", {}, `“${e.review_quote}”`),
      h("div", { class: "source" }, e.review_source)) : "",
    h("p", { class: "source" }, e.source),
    h("button", { class: kept ? "" : "secondary", "aria-pressed": String(kept), onclick: () => keep(e) },
      kept ? "✓ In my request" : "Add to my request"),
  );
}

function keep(e) {
  if (state.chosen.has(e.id)) state.chosen.delete(e.id);
  else {
    state.chosen.add(e.id);
    state.wantedType ??= e.type_code;
  }
  renderResults();
}

function renderChanges(changes) {
  if (!changes) return $("#changes").replaceChildren();
  const o = state.options;
  const fmt = (field, v) => Array.isArray(v) ? v.map((x) => label(o[field] || {}, x)).join(", ") || "none"
    : field === "pace" ? label(o.paces, v) : field === "destination_id" ? state.destinations.find((d) => d.id === v)?.name : v ?? "–";
  const nothing = !changes.added.length && !changes.removed.length && !changes.reasons_changed.length;
  $("#changes").replaceChildren(h("div", { class: "card changes" },
    h("h3", {}, "What changed"),
    h("ul", {},
      changes.changed_preferences.map((c) => h("li", {}, `${c.field.replace("_", " ")}: ${fmt(c.field, c.from)} → ${fmt(c.field, c.to)}`)),
      changes.added.length ? h("li", {}, h("strong", {}, "New: "), changes.added.join(", ")) : "",
      changes.removed.length ? h("li", {}, h("strong", {}, "No longer shown: "), changes.removed.join(", ")) : "",
      changes.reasons_changed.length ? h("li", {}, h("strong", {}, "Same suggestion, new reasons: "), changes.reasons_changed.join(", ")) : "",
      nothing ? h("li", {}, "Your suggestions stayed the same – they still fit best.") : "")));
}

// K7: documented value, close to the decision
function renderWhyAmitylux() {
  $("#why-amitylux").replaceChildren(
    h("h2", {}, "Why book with Amitylux?"),
    h("ul", { class: "list" }, state.claims.map((c) =>
      h("li", {}, h("strong", {}, c.label), " – ", c.text, h("div", { class: "source" }, `Source: ${c.evidence}`)))));
}

// K3: change one preference and see the result update
$("#adjust-form").addEventListener("change", async (e) => {
  const before = structuredClone(state.prefs);
  const { name, value } = e.target;
  state.prefs[name] = name === "group_size" ? Number(value) : value;
  try {
    await fetchSuggestions();
  } catch {
    state.prefs = before;
  }
  renderPreferenceInputs();
  renderActiveChoices();
});

// Interests and practical needs are changed in step 2; the summary step then shows what changed
$("#adjust-interests").addEventListener("click", () => goTo("preferences"));

// ---------------------------------------------------------------- Step 5: K4 compare
function renderCompare() {
  const rows = [["What it is", "short"], ["Group", "group_form"], ["Flexibility", "flexibility"],
    ["Personalisation", "personalisation"], ["How to book", "booking_form"], ["Price principle", "price_principle"],
    ["Best for", "best_for"]];
  renderTable($("#compare-table"), rows.map(([title, key]) => ({ title, key })), [
    { label: "", render: (r) => h("strong", {}, r.title) },
    ...state.types.map((t) => ({ label: t.name, render: (r) => t[r.key] })),
  ]);
  radioChips($("#wanted-type-choices"), "wanted_type", state.types.map((t) => [t.code, t.name]), state.wantedType,
    (v) => { state.wantedType = v; });
}

// ---------------------------------------------------------------- Step 6: K8 request with preview
function requestBody() {
  return {
    ...state.prefs,
    ...formToJson($("#request-form")),
    wanted_type: state.wantedType,
    experience_ids: [...state.chosen],
    addons: state.chosenAddons,
  };
}

function renderRequest() {
  const titles = state.result?.suggestions.filter((s) => state.chosen.has(s.experience.id)).map((s) => s.experience.title) || [];
  $("#kept-info").textContent = `Your answers are already included${titles.length ? `, together with: ${titles.join(", ")}` : ""}. You will not be asked the same questions again.`;
  radioChips($("#addon-choices"), "addons", state.addons.map((a) => [a.code, a.name]), state.chosenAddons,
    (v, on) => { state.chosenAddons = toggle(state.chosenAddons, v, on); previewBrief(); }, "checkbox");
  $("#receipt").replaceChildren();
  previewBrief();
}

let previewTimer;
function previewBrief() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(async () => {
    const brief = await api("/inquiries/preview", { method: "POST", body: requestBody() }).catch((err) => toast(err.message, "error"));
    if (brief) $("#brief-preview").replaceChildren(renderBrief(brief));
  }, 200);
}

$("#request-form").addEventListener("input", previewBrief);

$("#request-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const result = await run(() => api("/inquiries", { method: "POST", body: requestBody() }), (r) => `Request ${r.receipt.reference} sent`);
  $("#brief-preview").replaceChildren(renderBrief(result.brief));
  $("#receipt").replaceChildren(h("div", { class: "card highlight" },
    h("h3", {}, `Receipt – ${result.receipt.reference}`),
    h("p", {}, result.receipt.message),
    h("ol", {}, result.receipt.next_steps.map((s) => h("li", {}, s)))));
  $("#receipt").scrollIntoView({ behavior: "smooth" });
});

function renderBrief(b) {
  const section = (title, obj) => h("div", {},
    h("h3", {}, title),
    h("ul", { class: "list" }, Object.entries(obj).map(([k, v]) =>
      h("li", {}, h("strong", {}, `${k.replace("_", " ")}: `), Array.isArray(v) ? v.join(", ") || "–" : v ?? "–"))));
  return h("div", {},
    h("p", {}, badge(b.reference), " ", badge(b.status, STATUS_BADGE[b.status] ?? "muted"), " ", badge(b.wanted_type, "muted"),
      b.received ? h("span", { class: "muted" }, ` ${formatDate(b.received)}`) : ""),
    section("Customer", b.customer),
    section("Trip", b.trip),
    section("Preferences", b.preferences),
    section("Selected", { ...b.selected, notes: b.notes }),
    h("h3", {}, "Requires confirmation"),
    b.uncertainties.length ? h("ul", {}, b.uncertainties.map((u) => h("li", {}, u))) : h("p", { class: "muted" }, "None"),
    h("p", {}, h("strong", {}, "Next step: "), b.next_action));
}

// ---------------------------------------------------------------- K8 Talk to a person (from any step)
$("#help-button").addEventListener("click", () => $("#help-dialog").showModal());
$("#help-close").addEventListener("click", () => $("#help-dialog").close());
$("#help-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const step = $(`#step-${state.step}`).dataset.title;
  const answers = { ...state.prefs, kept_experience_ids: [...state.chosen], wanted_type: state.wantedType };
  await run(() => api("/help-requests", { method: "POST", body: { ...formToJson(event.target), step, answers } }),
    "Thank you – a local expert will contact you. Your answers are kept.");
  $("#help-dialog").close();
  event.target.reset();
});

// ---------------------------------------------------------------- Staff view
$("#staff-button").addEventListener("click", () => {
  const staff = $("#staff-view").hidden;
  $("#staff-view").hidden = !staff;
  $("#customer-view").hidden = staff;
  $("#staff-button").textContent = staff ? "Customer view" : "Staff view";
  if (staff) loadStaff();
});

async function loadStaff() {
  const [inquiries, help, audit] = await Promise.all([api("/inquiries"), api("/help-requests"), api("/catalogue/audit")]);
  renderTable($("#inquiry-table"), inquiries, [
    { label: "Ref.", key: "reference" },
    { label: "Customer", key: "contact_name" },
    { label: "Type", render: (i) => label(state.options.types, i.wanted_type) },
    { label: "Received", render: (i) => formatDate(i.created_at) },
    { label: "Status", render: (i) => badge(i.status, STATUS_BADGE[i.status]) },
    {
      label: "",
      render: (i) => h("div", { class: "actions" },
        h("button", { class: "small secondary", onclick: async () => $("#brief").replaceChildren(renderBrief(await api(`/inquiries/${i.id}/brief`))) }, "Brief"),
        h("select", {
          class: "small", "aria-label": "Status",
          onchange: async (e) => {
            await run(() => api(`/inquiries/${i.id}`, { method: "PUT", body: { status: e.target.value } }), "Status updated");
            loadStaff();
          },
        }, ["NEW", "IN_PROGRESS", "ANSWERED", "CLOSED"].map((s) => h("option", { value: s, selected: s === i.status }, s)))),
    },
  ], "No requests yet");
  renderTable($("#help-table"), help, [
    { label: "Name", key: "name" }, { label: "Contact", key: "contact" }, { label: "Step", key: "step" },
    { label: "Answers kept", render: (x) => summariseAnswers(JSON.parse(x.answers || "{}")) },
    { label: "Received", render: (x) => formatDate(x.created_at) },
  ], "No help requests");
  renderTable($("#audit-table"), audit, [
    { label: "Experience", render: (a) => [h("strong", {}, a.title), h("div", { class: "muted" },
      `${state.destinations.find((d) => d.id === a.destination_id)?.name} · ${a.type_name}`)] },
    { label: "Status", render: (a) => a.used_in_suggestions ? badge("Used", "ok") : badge(a.problems.join("; "), "danger") },
    { label: "Approved", render: (a) => a.approved_by ? `${a.approved_at} · ${a.approved_by}` : "–" },
    { label: "Always shown as requires confirmation", render: (a) => a.requires_confirmation.join(", ") || "–" },
  ]);
}

function summariseAnswers(a) {
  const o = state.options;
  const destination = state.destinations.find((d) => d.id === a.destination_id)?.name;
  return [destination, a.group_type && `${a.group_size} · ${label(o.group_types, a.group_type)}`,
    (a.interests || []).map((i) => label(o.interests, i)).join(", "), a.pace, a.language]
    .filter(Boolean).join(" · ") || "–";
}

// ---------------------------------------------------------------- Start
async function start() {
  const [options, destinations, types, addons, claims] = await Promise.all([
    api("/options"), api("/destinations"), api("/product-types"), api("/addons"), api("/value-claims")]);
  Object.assign(state, { options, destinations, types, addons, claims });
  renderPreferenceInputs();
  renderCompare();
  goTo("start");
}

start().catch((err) => toast(`Cannot reach the backend: ${err.message}`, "error"));
