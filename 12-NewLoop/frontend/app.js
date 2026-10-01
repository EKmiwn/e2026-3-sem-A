// LoopAAS – præsentationslag. Henter JSON fra Flask-API'et og viser det i DOM'en.

const state = { userId: null, profile: null, partners: [] };

const TYPE_ICON = { KOP: "☕", SKÅL: "🥣", BOKS: "🍱" };

function kpi(value, label) {
  return h("div", { class: "kpi" }, h("div", { class: "value" }, value ?? "–"), h("div", { class: "label" }, label));
}

function goTo(tab) {
  document.querySelector(`.tabs button[data-tab="${tab}"]`).click();
}

// ---------------------------------------------------------------- Indlæsning
async function loadBase() {
  const [users, locations, partners] = await Promise.all([api("/users"), api("/locations"), api("/partners")]);
  state.partners = partners;
  const previous = state.userId;
  fillSelect($("#user-select"), users, (u) => u.name);
  if (previous) $("#user-select").value = previous;
  state.userId = Number($("#user-select").value);
  fillSelect($("#return-form [name=location_id]"), locations, (l) => `${l.name}${l.kind === "RETURPUNKT" ? " (returstander)" : ""}`);
  fillSelect($("#partner-select"), partners, (p) => p.name);
  fillSelect($("#reward-form [name=partner_id]"), partners, (p) => p.name);
}

// ---------------------------------------------------------------- Min side (FR04)
async function loadMe() {
  const p = await api(`/users/${state.userId}/profile`);
  state.profile = p;
  $("#hello").textContent = `Hej ${p.user.name.split(" ")[0]} 👋`;
  $("#points").textContent = p.points.toLocaleString("da-DK");
  $("#level-title").textContent = `${p.level.icon} Niveau ${p.level.name}`;
  $("#level-bar").style.width = `${p.level.progress_pct}%`;
  $("#level-text").textContent = p.level.next
    ? `${p.level.points_to_next} point mere til ${p.level.next} (${p.level.total_earned} optjent i alt)`
    : "Du har nået det højeste niveau 🎉";
  $("#me-kpis").replaceChildren(
    kpi(p.returns, "emballager returneret"),
    kpi(`${p.week_streak} 🔥`, "uger i træk"),
    kpi(`${p.co2_saved_kg} kg`, "CO₂ sparet (anslået)"));
  $("#badges").replaceChildren(...p.badges.map((b) => h("div", { class: `badge-card ${b.earned ? "" : "locked"}`, title: b.goal },
    h("div", { class: "icon" }, b.icon), h("strong", {}, b.name), h("small", {}, b.earned ? "Optjent" : b.goal))));
}

$("#return-cta").addEventListener("click", () => goTo("return"));

// ---------------------------------------------------------------- Returnér (FR02, FR03)
async function loadOpenCodes() {
  const codes = await api("/packages/open");
  $("#open-codes").replaceChildren(...codes.slice(0, 10).map((c) => h("button", {
    class: "small secondary", type: "button", title: c.location,
    onclick: () => { $("#return-form").elements.code.value = c.code; },
  }, `${TYPE_ICON[c.type]} ${c.code}`)));
}

$("#return-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const box = $("#return-result");
  try {
    const r = await api("/returns", { method: "POST", body: { ...formToJson(event.target), user_id: state.userId } });
    box.replaceChildren(h("div", { class: "card result ok" },
      h("div", { class: "plus" }, `+${r.points_earned}`),
      h("p", {}, r.message),
      h("p", {}, `Ny saldo: ${r.new_balance} LoopPoints`),
      r.level_up ? h("p", {}, h("strong", {}, `🎉 Nyt niveau: ${r.level_up}!`)) : null,
      ...r.new_badges.map((b) => h("p", {}, h("strong", {}, `${b.icon} Ny badge: ${b.name}`)))));
    toast(`+${r.points_earned} LoopPoints`);
    event.target.elements.code.value = "";
  } catch (err) {
    box.replaceChildren(h("div", { class: "card result error" }, h("strong", {}, "Returneringen blev ikke godkendt"), h("p", {}, err.message)));
    toast(err.message, "error");
  }
  loadOpenCodes();
  loadMe();
});

// ---------------------------------------------------------------- Rewards (FR05 – FR08)
async function loadRewards() {
  const rewards = await api(`/catalog?user_id=${state.userId}`);
  $("#reward-balance").textContent = `Du har ${state.profile?.points ?? "–"} LoopPoints.`;
  $("#rewards").replaceChildren(...rewards.map((r) => h("div", { class: "card reward" },
    h("div", { class: "muted" }, `${r.partner} · ${r.category}`),
    h("h3", { style: "margin:4px 0" }, r.name),
    r.description ? h("p", { class: "muted", style: "margin:0" }, r.description) : null,
    h("div", { class: "cost" }, `${r.points_required} point`),
    r.stock !== null ? h("small", { class: "muted" }, r.sold_out ? "Udsolgt" : `${r.stock} tilbage`) : null,
    h("div", { class: "level-bar" }, h("span", { style: `width:${Math.min(100, Math.round((100 * (r.points_required - r.missing_points)) / r.points_required))}%` })),
    r.can_redeem
      ? h("button", { onclick: () => redeem(r) }, "Indløs")
      : h("button", { class: "secondary", disabled: true }, r.sold_out ? "Udsolgt" : `Mangler ${r.missing_points} point`))));
}

async function redeem(reward) {
  if (!confirm(`Indløs ${reward.name} for ${reward.points_required} LoopPoints?`)) return;
  const r = await run(() => api("/redemptions", { method: "POST", body: { user_id: state.userId, reward_id: reward.id } }), "Reward indløst");
  $("#redeem-result").replaceChildren(h("div", { class: "card highlight", style: "text-align:center" },
    h("p", {}, `Vis denne kode hos ${r.partner}:`),
    h("div", { class: "code" }, r.redemption.code),
    h("p", {}, r.message),
    h("p", { class: "muted" }, `Ny saldo: ${r.new_balance} LoopPoints · koden findes også under Historik`)));
  await loadMe();
  loadRewards();
}

// ---------------------------------------------------------------- Historik (FR09)
async function loadHistory() {
  const h_ = await api(`/users/${state.userId}/history`);
  $("#active-codes").replaceChildren(...(h_.active_codes.length ? [h("div", { class: "card highlight" },
    h("h2", {}, "Klar til brug"),
    ...h_.active_codes.map((c) => h("p", {}, h("span", { class: "code", style: "font-size:1.2rem" }, c.code), ` · ${c.type} hos ${c.place}`)))] : []));
  $("#history").replaceChildren(...(h_.history.length ? h_.history.map((r) => h("div", { class: "history-row" },
    h("div", {},
      h("strong", {}, r.kind === "RETUR" ? `${TYPE_ICON[r.type]} Returneret ${r.type.toLowerCase()}` : `🎁 ${r.type}`),
      h("div", { class: "muted" }, `${formatDate(r.time)} · ${r.place}`, r.status ? " · " : "", r.status ? badge(r.status.toLowerCase(), r.status === "AKTIV" ? "ok" : "muted") : null)),
    h("div", { class: `pts ${r.points > 0 ? "plus" : "minus"}` }, `${r.points > 0 ? "+" : ""}${r.points}`)))
    : [h("p", { class: "empty" }, "Ingen historik endnu – returnér din første emballage.")]));
}

// ---------------------------------------------------------------- Samarbejdspartner
$("#verify-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const box = $("#verify-result");
  try {
    const r = await api("/redemptions/verify", { method: "POST", body: { ...formToJson(event.target), partner_id: Number($("#partner-select").value) } });
    box.replaceChildren(h("div", { class: "result ok", style: "margin-top:12px" }, h("strong", {}, `✔ ${r.message}`)));
    event.target.reset();
  } catch (err) {
    box.replaceChildren(h("div", { class: "result error", style: "margin-top:12px" }, h("strong", {}, `✖ ${err.message}`)));
  }
});

async function loadPartnerAdmin() {
  const rewards = await api("/rewards");
  const partnerName = Object.fromEntries(state.partners.map((p) => [p.id, p.name]));
  renderTable($("#reward-table"), rewards, [
    { label: "Reward", key: "name" },
    { label: "Partner", render: (r) => partnerName[r.partner_id] },
    { label: "Point", class: "num", key: "points_required" },
    { label: "Lager", class: "num", render: (r) => r.stock ?? "∞" },
    { label: "Aktiv", render: (r) => (r.active ? badge("ja", "ok") : badge("nej", "muted")) },
    { label: "", render: (r) => crudButtons("rewards", $("#reward-form"), r, loadPartnerAdmin) },
  ]);
}

bindCrudForm($("#reward-form"), "rewards", loadPartnerAdmin);

// ---------------------------------------------------------------- New Loop
async function loadNewLoop() {
  const [s, partners, settings] = await Promise.all([api("/stats"), api("/partners"), api("/settings")]);
  $("#stats-kpis").replaceChildren(
    kpi(s.users, "brugere"),
    kpi(s.packages_issued, "emballager udleveret"),
    kpi(`${s.return_rate_pct} %`, "returrate"),
    kpi(s.returns_30d, "returneringer (30 dage)"),
    kpi(s.points_earned.toLocaleString("da-DK"), "point optjent"),
    kpi(s.points_redeemed.toLocaleString("da-DK"), "point brugt på rewards"));
  $("#leaderboard").replaceChildren(...s.leaderboard.map((u) => h("li", {}, `${u.name} – ${u.returns} returneringer`)));
  renderTable($("#partner-stats"), s.per_partner, [
    { label: "Partner", key: "name" },
    { label: "Indløst", class: "num", key: "redemptions" },
    { label: "Brugt", class: "num", key: "used" },
  ]);
  renderTable($("#partner-table"), partners, [
    { label: "Navn", key: "name" },
    { label: "Kategori", key: "category" },
    { label: "", render: (p) => crudButtons("partners", $("#partner-form"), p, reloadEverything) },
  ]);
  renderTable($("#setting-table"), settings, [
    { label: "Nøgle", key: "key" },
    { label: "Værdi", class: "num", key: "value" },
    { label: "Beskrivelse", key: "description" },
    { label: "", render: (x) => h("button", { class: "small secondary", onclick: () => fillForm($("#setting-form"), x) }, "Redigér") },
  ]);
}

bindCrudForm($("#partner-form"), "partners", reloadEverything);
bindCrudForm($("#setting-form"), "settings", loadNewLoop);
bindCrudForm($("#user-form"), "users", reloadEverything);

// ---------------------------------------------------------------- Start
function reloadEverything() {
  return loadBase().then(loadAll);
}

function loadAll() {
  return Promise.all([loadMe(), loadOpenCodes(), loadHistory(), loadPartnerAdmin(), loadNewLoop()]);
}

$("#user-select").addEventListener("change", (event) => {
  state.userId = Number(event.target.value);
  loadAll();
});

setupTabs((tab) => {
  ({ me: loadMe, rewards: loadRewards, history: loadHistory, newloop: loadNewLoop })[tab]?.();
});
loadBase()
  .then(loadAll)
  .catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
