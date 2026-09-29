// Amitylux – presentation layer. Fetches JSON from the Flask API and shows it in the DOM.

const state = { destinations: [], addons: [], prefs: null, recommendation: null, selectedExperience: null };

const STATUS_BADGE = { NEW: "warn", IN_PROGRESS: "", ANSWERED: "ok", CLOSED: "muted" };

function goTo(tab) {
  document.querySelector(`.tabs [data-tab="${tab}"]`).click();
}

// ---------------------------------------------------------------- Load
async function loadBase() {
  const [destinations, addons, types] = await Promise.all([api("/destinations"), api("/addons"), api("/product-types")]);
  Object.assign(state, { destinations, addons });
  fillSelect($("#needs-form [name=destination_id]"), destinations, (d) => `${d.name}, ${d.country}`);
  $("#addon-list").append(...addons.map((a) =>
    h("label", {}, h("input", { type: "checkbox", name: "addons", value: a.code, "data-list": true }),
      `${a.name} `, h("span", { class: "muted" }, `(${a.price_hint})`))));
  renderComparison(types);
  searchExperiences();
}

// ---------------------------------------------------------------- F-02 Comparison
function renderComparison(types) {
  const rows = [
    ["Group", "group_form"], ["Flexibility", "flexibility"], ["Personalisation", "personalisation"],
    ["Price principle", "price_principle"], ["How to book", "booking_form"],
    ["Included", "included"], ["Not included", "not_included"],
  ];
  renderTable($("#compare-table"), rows.map(([label, key]) => ({ label, key })), [
    { label: "", render: (r) => h("strong", {}, r.label) },
    ...types.map((t) => ({ label: t.name, render: (r) => t[r.key] })),
  ]);
}

// ---------------------------------------------------------------- F-01 → F-03 Recommendation
$("#needs-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  state.prefs = formToJson(event.target);
  state.recommendation = await run(() => api("/recommendations", { method: "POST", body: state.prefs }));
  renderRecommendation();
  renderSummary();
  goTo("recommend");
});

document.querySelectorAll("[data-goto]").forEach((b) => b.addEventListener("click", () => goTo(b.dataset.goto)));

function renderRecommendation() {
  const r = state.recommendation;
  const p = r.based_on;
  $("#recommendation").replaceChildren(
    // NF-04 transparency: show what the recommendation is based on, and let the user change it
    h("div", { class: "card" },
      h("strong", {}, "Based on your answers: "),
      [r.destination.name, `${p.group_size} × ${p.group_type}`, `${p.pace} pace`, `${p.budget} budget`,
        p.language, ...(p.interests || [])].map((v) => [badge(v), " "]),
      h("button", { class: "small secondary", onclick: () => goTo("needs") }, "Change answers")),

    r.capacity_warning && h("div", { class: "card", style: "border-color: var(--warn)" },
      h("strong", {}, "Heads-up on availability: "), r.capacity_warning.messages.join(" "),
      h("p", { class: "muted" }, r.capacity_warning.suggestion)),

    optionCard(r.primary, true),
    h("div", { class: "grid wide" }, r.alternatives.map((alt) => optionCard(alt, false))),

    r.less_crowded_alternative && h("div", { class: "card" },
      h("h3", {}, "Away from the crowds"),
      h("p", { class: "muted" }, r.less_crowded_alternative.reason),
      experienceCard(r.less_crowded_alternative)),

    r.contextual_suggestions.length > 0 && h("div", { class: "card" },
      h("h3", {}, "You might also like"),
      h("ul", { class: "list" }, r.contextual_suggestions.map((s) =>
        h("li", {}, h("strong", {}, s.name), " – ", s.description,
          s.kind === "destination" ? h("span", { class: "muted" }, ` (${s.country})`) : "")))),
  );
}

function optionCard(option, primary) {
  return h("div", { class: `card ${primary ? "highlight" : ""}` },
    h("p", { class: "muted" }, primary ? "Our recommendation for you" : "Alternative"),
    h("h2", {}, option.type_name),
    h("ul", {}, option.reasons.slice(0, primary ? 4 : 2).map((reason) => h("li", {}, reason))),
    h("div", { class: "grid" }, option.experiences.map(experienceCard)),
  );
}

// NF-05: the same product card structure is used for every destination
function experienceCard(e) {
  return h("div", { class: "card" },
    h("p", {}, badge(e.type_name), " ", e.sustainable_label ? badge(`🌿 ${e.sustainable_label}`, "ok") : ""),
    h("h3", {}, e.title),
    h("p", {}, e.description),
    h("p", {}, h("strong", {}, e.price_label), h("span", { class: "muted" }, ` · ${e.duration_hours} h · ${e.min_group}–${e.max_group} people`)),
    h("p", { class: "muted" }, `✔ Included: ${e.included}`),
    h("p", { class: "muted" }, `✖ Not included: ${e.not_included}`),
    h("p", {}, e.value_points.map((v) => [badge(v, "ok"), " "])),
    h("p", {}, `★ ${e.rating} (${e.review_count} reviews) `, h("em", {}, e.review_quote)),
    h("p", { class: "muted" }, `Your guide: ${e.guide_name} – ${e.guide_expertise}. Languages: ${e.languages.join(", ")}`),
    h("button", { class: "small", onclick: () => chooseExperience(e) }, "Choose and continue"),
  );
}

function chooseExperience(experience) {
  state.selectedExperience = experience;
  renderSummary();
  goTo("request");
}

// ---------------------------------------------------------------- F-04 Filters
async function searchExperiences() {
  const filters = formToJson($("#filter-form"));
  const destination = state.prefs?.destination_id;
  if (destination) filters.destination_id = destination;
  const query = new URLSearchParams(filters).toString();
  const result = await api(`/experiences/search?${query}`);
  const active = Object.entries(result.active_filters);
  $("#active-filters").textContent = active.length
    ? `Active filters: ${active.map(([k, v]) => `${k} = ${v}`).join(", ")} · ${result.results.length} results`
    : `${result.results.length} experiences`;
  $("#experience-cards").replaceChildren(...result.results.map(experienceCard));
}

$("#filter-form").addEventListener("change", searchExperiences);
$("#filter-form").addEventListener("reset", () => setTimeout(searchExperiences));

// ---------------------------------------------------------------- F-07, F-08 Summary and send
function requestData() {
  const extra = formToJson($("#request-form"));
  return {
    ...(state.prefs || formToJson($("#needs-form"))),
    ...extra,
    experience_id: state.selectedExperience?.id,
    recommended_type: state.recommendation?.primary.type_code,
  };
}

function renderSummary() {
  const d = requestData();
  const destination = state.destinations.find((x) => x.id === d.destination_id);
  const rows = [
    ["Destination", destination?.name], ["Dates", [d.date_from, d.date_to].filter(Boolean).join(" → ")],
    ["Group", `${d.group_size ?? "?"} · ${d.group_type ?? ""}`], ["Language", d.language],
    ["Pace", d.pace], ["Budget", d.budget], ["Interests", (d.interests || []).join(", ")],
    ["Recommended", state.recommendation?.primary.type_name], ["Chosen experience", state.selectedExperience?.title],
    ["Add-ons", (d.addons || []).map((code) => state.addons.find((a) => a.code === code)?.name).join(", ")],
    ["Guide wishes", [d.guide_language, d.guide_focus, d.guide_style].filter(Boolean).join(" · ")],
    ["Notes", d.notes], ["Contact", [d.contact_name, d.contact_email, d.contact_phone].filter(Boolean).join(" · ")],
  ];
  renderTable($("#summary"), rows.map(([label, value]) => ({ label, value: value || "–" })), [
    { label: "Field", key: "label" }, { label: "Your answer", key: "value" },
  ]);
}

$("#request-form").addEventListener("input", renderSummary);
$("#request-form").addEventListener("change", renderSummary);

$("#request-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const result = await run(() => api("/inquiries", { method: "POST", body: requestData() }),
    (r) => `Request ${r.receipt.reference} sent`);
  $("#receipt").replaceChildren(h("div", { class: "card highlight" },
    h("h3", {}, `Receipt – ${result.receipt.reference}`),
    h("p", {}, result.receipt.message),
    h("ol", {}, result.receipt.next_steps.map((s) => h("li", {}, s)))));
  loadStaff();
});

// ---------------------------------------------------------------- F-09 Personal help
$("#help-button").addEventListener("click", () => $("#help-dialog").showModal());
$("#help-close").addEventListener("click", () => $("#help-dialog").close());
$("#help-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const step = document.querySelector(".tabs button.active").textContent;
  await run(() => api("/help-requests", { method: "POST", body: { ...formToJson(event.target), step } }),
    "Thank you – a local expert will contact you shortly");
  $("#help-dialog").close();
  event.target.reset();
  loadStaff();
});

// ---------------------------------------------------------------- F-15 Staff view
async function loadStaff() {
  const [inquiries, help] = await Promise.all([api("/inquiries"), api("/help-requests")]);
  renderTable($("#inquiry-table"), inquiries, [
    { label: "Ref.", key: "reference" },
    { label: "Customer", key: "contact_name" },
    { label: "Received", render: (i) => formatDate(i.created_at) },
    { label: "Status", render: (i) => badge(i.status, STATUS_BADGE[i.status]) },
    {
      label: "",
      render: (i) => h("div", { class: "actions" },
        h("button", { class: "small secondary", onclick: () => showBrief(i.id) }, "Brief"),
        h("select", {
          class: "small",
          onchange: async (e) => {
            await run(() => api(`/inquiries/${i.id}`, { method: "PUT", body: { status: e.target.value } }), "Status updated");
            loadStaff();
          },
        }, ["NEW", "IN_PROGRESS", "ANSWERED", "CLOSED"].map((s) => h("option", { value: s, selected: s === i.status }, s)))),
    },
  ]);
  renderTable($("#help-table"), help, [
    { label: "Name", key: "name" }, { label: "Contact", key: "contact" },
    { label: "Step", key: "step" }, { label: "Received", render: (x) => formatDate(x.created_at) },
  ], "No help requests");
}

async function showBrief(id) {
  const b = await api(`/inquiries/${id}/brief`);
  const section = (title, obj) => h("div", {},
    h("h3", {}, title),
    h("ul", { class: "list" }, Object.entries(obj).map(([k, v]) =>
      h("li", {}, h("strong", {}, `${k.replace("_", " ")}: `), Array.isArray(v) ? v.join(", ") || "–" : v ?? "–"))));
  $("#brief").replaceChildren(
    h("p", {}, badge(b.reference), " ", badge(b.status, STATUS_BADGE[b.status]), " ", h("span", { class: "muted" }, formatDate(b.received))),
    section("Customer", b.customer),
    section("Trip", b.trip),
    section("Preferences", b.preferences),
    section("Guide wishes", b.guide_wishes),
    section("Request", { add_ons: b.add_ons, selected_experience: b.selected_experience, recommended_type: b.recommended_type, free_text: b.free_text }),
    h("h3", {}, "Uncertainties"),
    b.uncertainties.length ? h("ul", {}, b.uncertainties.map((u) => h("li", {}, u))) : h("p", { class: "muted" }, "None"),
    h("p", {}, h("strong", {}, "Next action: "), b.next_action),
  );
}

// ---------------------------------------------------------------- Start
setupTabs((tab) => { if (tab === "request") renderSummary(); });
loadBase()
  .then(loadStaff)
  .then(renderSummary)
  .catch((err) => toast(`Cannot reach the backend: ${err.message}`, "error"));
