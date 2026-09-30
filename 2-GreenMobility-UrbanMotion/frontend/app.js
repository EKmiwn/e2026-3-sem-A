// GreenMobility Hotspot – kundeside (præsentationslag). Henter JSON fra Flask-API'et og viser det i DOM'en.
// Den indloggede kunde vælges i prototypen med ?kunde=2 i adressen (standard: kunde 1). Se admin.html.

const state = {
  customerId: Number(new URLSearchParams(location.search).get("kunde")) || 1,
  customer: null,
  info: null,
  hotspots: [],
  reservations: [],
  query: "",
  position: null,        // brugerens position – kun i browseren, sendes ikke til serveren
  arrived: null,         // seneste ankomst, vises som kvittering indtil den lukkes
  aiMessages: [{ from: "ai", text: "Hej! Jeg er GreenMobilitys AI-assistent. Spørg mig om booking, parkering eller problemer med appen." }],
  chatTimer: null,
};

const RES_STATUS = { AKTIV: ["Aktiv", "ok"], BENYTTET: ["Benyttet", ""], ANNULLERET: ["Annulleret", "muted"], UDLOEBET: ["Udløbet", "danger"] };

// ---------------------------------------------------------------- Indlæsning
async function load() {
  const [hotspots, reservations] = await Promise.all([
    api("/hotspots/overview"),
    api(`/reservations?customer_id=${state.customerId}`),
  ]);
  Object.assign(state, { hotspots, reservations });
  renderReservation();
  renderHotspots();
}

function activeReservation() {
  return state.reservations.find((r) => r.status === "AKTIV");
}

// ---------------------------------------------------------------- Aktiv reservation
function renderReservation() {
  const active = activeReservation();
  const box = $("#my-reservation");
  if (!active) {
    box.replaceChildren(state.arrived
      ? h("div", { class: "notice" },
          h("p", {}, h("strong", {}, "Du er parkeret. "), `Plads ${state.arrived.spot_label} ved ${state.arrived.hotspot_name} står nu som optaget.`),
          h("button", { class: "ghost small", onclick: () => { state.arrived = null; renderReservation(); } }, "OK"))
      : "");
    return;
  }
  box.replaceChildren(
    h("div", { class: "reservation" },
      h("div", { class: "eyebrow" }, `Din reservation · ${active.reservation_no}`),
      h("div", { class: "top" },
        h("div", { class: "spot-label", "aria-label": `Plads ${active.spot_label}` }, h("div", {}, h("small", {}, "PLADS"), active.spot_label)),
        h("div", { class: "where" }, h("strong", {}, active.hotspot_name), h("span", {}, active.hotspot_address))),
      h("div", { class: "timer" },
        h("span", { class: "left", id: "countdown" }, countdown(active.arrival_deadline)),
        h("span", { class: "deadline" }, `Ankom senest kl. ${active.arrival_deadline.slice(11, 16)}`)),
      h("div", { class: "bar", id: "countdown-bar" }, h("div", { style: `width:${progress(active)}%` })),
      h("div", { class: "actions" },
        h("button", { onclick: () => arrive(active) }, "Jeg er ankommet"),
        h("button", { class: "danger-outline", onclick: () => confirmCancel(active) }, "Annullér")),
      h("div", { class: "links" },
        h("button", { class: "ghost small", onclick: () => openHelp("problem") }, "Problem med pladsen?"),
        active.hotspot_directions && h("button", { class: "ghost small", onclick: () => showDirections(active) }, "Vejvisning"))),
  );
  tick();
}

function msLeft(deadline) {
  return new Date(deadline.replace(" ", "T")) - Date.now();
}

function countdown(deadline) {
  const ms = msLeft(deadline);
  if (ms <= 0) return "Udløbet";
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function progress(r) {
  const total = new Date(r.arrival_deadline.replace(" ", "T")) - new Date(r.created_at.replace(" ", "T"));
  return Math.max(0, Math.min(100, (msLeft(r.arrival_deadline) / total) * 100));
}

// Opdaterer nedtællingen hvert sekund og henter ny status, når fristen er nået
function tick() {
  const active = activeReservation();
  const el = $("#countdown");
  if (!active || !el) return;
  const soon = msLeft(active.arrival_deadline) < 5 * 60000;
  el.textContent = countdown(active.arrival_deadline);
  el.classList.toggle("soon", soon);
  $("#countdown-bar").classList.toggle("soon", soon);
  $("#countdown-bar > div").style.width = `${progress(active)}%`;
  if (el.textContent === "Udløbet") {
    toast("Din reservation er udløbet, og pladsen er givet videre.", "error");
    load();
  }
}
setInterval(tick, 1000);

async function arrive(r) {
  const done = await run(() => api(`/reservations/${r.id}/arrive`, { method: "POST" }), "Ankomst registreret – god parkering!");
  state.arrived = done;
  load();
}

function confirmCancel(r) {
  openSheet("Annullér reservation?",
    h("p", {}, `Plads ${r.spot_label} ved ${r.hotspot_name} bliver straks ledig for andre.`),
    h("ul", { class: "facts" }, h("li", {}, h("span", {}, "Pris for annullering"), h("span", {}, state.info.fees.cancel))),
    h("div", { class: "actions" },
      h("button", { class: "secondary", onclick: closeSheet }, "Behold"),
      h("button", { class: "danger", onclick: async () => {
        await run(() => api(`/reservations/${r.id}/cancel`, { method: "POST" }), "Reservationen er annulleret");
        closeSheet();
        load();
      } }, "Annullér")));
}

function showDirections(r) {
  openSheet(`Vejvisning · plads ${r.spot_label}`,
    h("p", {}, h("strong", {}, r.hotspot_name), h("br"), h("span", { class: "muted" }, r.hotspot_address)),
    h("p", {}, r.hotspot_directions),
    h("div", { class: "actions" },
      h("a", { class: "button secondary", target: "_blank", rel: "noopener",
               href: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.hotspot_address)}` }, "Åbn i kort"),
      h("button", { onclick: () => openHelp("problem") }, "Kan stadig ikke finde den")));
}

// ---------------------------------------------------------------- Hotspots
function distanceKm(a, b) {
  const rad = (d) => (d * Math.PI) / 180;
  const x = Math.sin(rad(b.lat - a.lat) / 2) ** 2
    + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(rad(b.lng - a.lng) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(x));
}

function formatKm(km) {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toLocaleString("da-DK", { maximumFractionDigits: 1 })} km`;
}

function visibleHotspots() {
  const q = state.query.trim().toLowerCase();
  let rows = state.hotspots.filter((hs) => !q || [hs.name, hs.address, hs.area].join(" ").toLowerCase().includes(q));
  if (state.position) {
    rows = rows.map((hs) => ({ ...hs, km: hs.lat == null ? null : distanceKm(state.position, hs) }))
      .sort((a, b) => (a.km ?? 1e9) - (b.km ?? 1e9));
  }
  return rows;
}

function renderHotspots() {
  const active = activeReservation();
  const rows = visibleHotspots();
  const totalFree = rows.reduce((sum, hs) => sum + hs.free, 0);

  $("#list-meta").textContent = active
    ? "Du har en aktiv reservation. Annullér den for at reservere et andet sted."
    : state.query
      ? `${rows.length} hotspot${rows.length === 1 ? "" : "s"} fundet`
      : `${totalFree} ledige pladser på ${rows.length} hotspots${state.position ? " · sorteret efter afstand" : ""}`;

  if (!rows.length) {
    $("#hotspot-list").replaceChildren(h("li", { class: "empty" }, `Intet hotspot matcher »${state.query}«.`));
    return;
  }
  $("#hotspot-list").replaceChildren(...rows.map((hs) => {
    const full = hs.free === 0;
    return h("li", { class: "hotspot" },
      h("div", { class: "text" },
        h("div", { class: "name" }, hs.name),
        h("div", { class: "address", title: hs.address }, hs.km != null ? `${formatKm(hs.km)} · ` : "", hs.address)),
      h("div", { class: "side" },
        h("span", { class: `free ${full ? "none" : hs.free <= 1 ? "few" : ""}` },
          full ? "Fuldt" : `${hs.free} ledig${hs.free === 1 ? "" : "e"} af ${hs.total}`),
        full
          ? h("button", { class: "secondary", onclick: () => showAlternatives(hs) }, "Alternativer")
          : h("button", { disabled: !!active, onclick: () => confirmBooking(hs) }, "Reservér")));
  }));
}

$("#search").addEventListener("input", (event) => {
  state.query = event.target.value;
  renderHotspots();
});

$("#near-me").addEventListener("click", () => {
  if (!navigator.geolocation) return toast("Din browser kan ikke finde din position", "error");
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      state.position = { lat: pos.coords.latitude, lng: pos.coords.longitude };
      renderHotspots();
    },
    () => toast("Vi fik ikke lov at bruge din position – listen er sorteret efter navn", "error"),
  );
});

// Gebyrer og regler vises, før kunden bekræfter
function confirmBooking(hs) {
  const fees = state.info.fees;
  openSheet(`Reservér ved ${hs.name}`,
    h("p", { class: "muted" }, hs.address),
    h("ul", { class: "facts" },
      h("li", {}, h("span", {}, "Pladsen holdes i"), h("span", {}, `${state.info.hold_minutes} minutter`)),
      h("li", {}, h("span", {}, "Pris for reservation"), h("span", {}, fees.reservation)),
      h("li", {}, h("span", {}, "Annullering"), h("span", {}, fees.cancel)),
      h("li", {}, h("span", {}, "Kommer du for sent"), h("span", {}, `Udløber · ${fees.no_show}`))),
    h("button", { class: "ghost small", onclick: showRules }, "Læs regler og vilkår"),
    h("div", { class: "actions" },
      h("button", { class: "secondary", onclick: closeSheet }, "Fortryd"),
      h("button", { onclick: () => book(hs) }, "Bekræft")));
}

async function book(hs) {
  try {
    const r = await api("/reservations", { method: "POST", body: { customer_id: state.customerId, hotspot_id: hs.id } });
    toast(`Plads ${r.spot_label} er reserveret til dig`);
    closeSheet();
    state.arrived = null;
    await load();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (err) {
    await load();
    const fresh = state.hotspots.find((x) => x.id === hs.id);
    if (fresh && fresh.free === 0) showAlternatives(fresh, "Den sidste plads blev taget lige før dig.");
    else toast(err.message, "error");
  }
}

async function showAlternatives(hs, reason) {
  const alternatives = await api(`/hotspots/${hs.id}/alternatives`);
  openSheet(`${hs.name} er fuldt`,
    h("p", {}, reason ? `${reason} ` : "", alternatives.length ? "Her er de nærmeste steder med ledige pladser:" : "Der er ingen ledige pladser andre steder lige nu."),
    h("ul", { class: "hotspots" }, alternatives.map((alt) =>
      h("li", { class: "hotspot" },
        h("div", { class: "text" },
          h("div", { class: "name" }, alt.name),
          h("div", { class: "address", title: alt.address }, alt.distance_km != null ? `${formatKm(alt.distance_km)} væk · ` : "", alt.address)),
        h("div", { class: "side" },
          h("span", { class: "free" }, `${alt.free} ledig${alt.free === 1 ? "" : "e"}`),
          h("button", { disabled: !!activeReservation(), onclick: () => confirmBooking(alt) }, "Reservér"))))));
}

// ---------------------------------------------------------------- Ark (dialog)
function openSheet(title, ...content) {
  stopChatPolling();
  $("#sheet-title").textContent = title;
  $("#sheet-body").replaceChildren(...content.flat(Infinity).filter(Boolean));
  if (!$("#sheet").open) $("#sheet").showModal();
}

function closeSheet() {
  $("#sheet").close();
}

$("#sheet-close").addEventListener("click", closeSheet);
$("#sheet").addEventListener("close", stopChatPolling);
$("#sheet").addEventListener("click", (event) => { if (event.target === $("#sheet")) closeSheet(); });   // klik på baggrunden

// ---------------------------------------------------------------- Menu: historik, regler, privatliv
const menu = $("#menu");
$("#menu-open").addEventListener("click", (event) => {
  event.stopPropagation();
  menu.hidden = !menu.hidden;
  $("#menu-open").setAttribute("aria-expanded", String(!menu.hidden));
});
document.addEventListener("click", () => { menu.hidden = true; });
menu.addEventListener("click", (event) => {
  const which = event.target.dataset.open;
  if (!which) return;
  menu.hidden = true;
  ({ history: showHistory, rules: showRules, privacy: showPrivacy })[which]();
});

function textSections(sections) {
  return sections.map((s) => [h("h3", {}, s.title), h("p", {}, s.text)]);
}

function showRules() {
  openSheet("Regler og vilkår", textSections(state.info.rules));
}

function showPrivacy() {
  openSheet("Privatliv", h("p", { class: "muted" }, "Kort fortalt: hvad appen gemmer, og hvad det bruges til."), textSections(state.info.privacy));
}

function showHistory() {
  openSheet("Mine reservationer", state.reservations.length
    ? h("ul", { class: "history" }, state.reservations.map((r) => {
        const [label, variant] = RES_STATUS[r.status];
        return h("li", {},
          h("div", {}, h("div", {}, `${r.hotspot_name} · plads ${r.spot_label}`), h("div", { class: "sub" }, `${r.reservation_no} · ${formatDate(r.created_at)}`)),
          h("div", {}, badge(label, variant)));
      }))
    : h("p", { class: "empty" }, "Du har ingen reservationer endnu."));
}

// ---------------------------------------------------------------- Hjælp: AI-chat, medarbejder, meld problem
$("#help-open").addEventListener("click", () => openHelp("ai"));

function openHelp(tab) {
  const tabs = [["ai", "AI-chat"], ["staff", "Medarbejder"], ["problem", "Meld problem"]];
  const body = h("div", {});
  openSheet("Hjælp",
    h("div", { class: "segmented", role: "tablist" }, tabs.map(([key, label]) =>
      h("button", { class: key === tab ? "active" : "", role: "tab", onclick: () => openHelp(key) }, label))),
    body);
  ({ ai: renderAiChat, staff: renderStaff, problem: renderProblem })[tab](body);
}

function chatMessage(from, text, extra) {
  const who = { ai: "AI-assistent", me: "Dig", staff: "Medarbejder", system: "" }[from];
  const cls = from === "me" ? "me" : from === "system" ? "system" : "them";
  return h("div", { class: `msg ${cls}` }, who && from !== "me" ? h("span", { class: "who" }, who) : null, text, extra);
}

function renderAiChat(body) {
  const list = h("div", { class: "chat", "aria-live": "polite" }, state.aiMessages.map((m) =>
    chatMessage(m.from, m.text, m.handoff ? h("div", {}, h("button", { class: "small", onclick: () => openHelp("staff") }, "Kontakt medarbejder")) : null)));
  const input = h("input", { placeholder: "Skriv dit spørgsmål …", "aria-label": "Spørgsmål til AI-assistenten" });

  async function ask(text) {
    if (!text.trim()) return;
    state.aiMessages.push({ from: "me", text });
    try {
      const res = await api("/assistant", { method: "POST", body: { text, customer_id: state.customerId } });
      state.aiMessages.push({ from: "ai", text: res.answer, handoff: res.handoff });
    } catch (err) {
      state.aiMessages.push({ from: "ai", text: "Jeg kunne ikke svare lige nu. Prøv igen, eller kontakt en medarbejder.", handoff: true });
    }
    openHelp("ai");
  }

  body.append(
    h("div", { class: "ai-note" }, "🤖 Du skriver med en AI-assistent, ikke et menneske. Svarene er automatiske og kan være forkerte."),
    list,
    state.aiMessages.length < 3 ? h("div", { class: "chips" },
      ["Hvor længe gælder en reservation?", "Hvordan annullerer jeg?", "Hvad hvis jeg kommer for sent?", "Koster det noget?"]
        .map((q) => h("button", { onclick: () => ask(q) }, q))) : "",
    h("form", { class: "composer", onsubmit: (event) => { event.preventDefault(); ask(input.value); } },
      input, h("button", {}, "Send")),
    h("div", { class: "links", style: "text-align:center;margin-top:8px" },
      h("button", { class: "ghost small", onclick: () => openHelp("staff") }, "Tal med en medarbejder i stedet")),
  );
  list.scrollTop = list.scrollHeight;
  if (window.matchMedia("(min-width: 601px)").matches) input.focus();
}

async function renderStaff(body) {
  const { support, staff } = state.info = await api("/info");   // hent friske åbningstider og hvem der er online
  const cases = await api(`/support?customer_id=${state.customerId}`);
  const open = cases.find((c) => c.status === "AABEN");

  body.append(
    h("p", {},
      h("span", { class: `pill ${support.open_now ? "open" : "closed"}` }, h("span", { class: `dot ${support.open_now ? "on" : ""}` }), support.open_now ? "Åbent nu" : "Lukket nu"),
      h("span", { class: "muted", style: "display:block;margin-top:4px" }, `Åbningstider: ${support.hours}`)),
    h("a", { class: "button secondary", style: "width:100%", href: `tel:${support.phone.replace(/\s/g, "")}` }, `Ring ${support.phone}`),
  );

  if (open) {
    body.append(h("h3", {}, `Din chat · ${open.case_no}${open.staff_name ? ` med ${open.staff_name}` : ""}`));
    renderCaseChat(body, open);
    return;
  }

  const input = h("textarea", { placeholder: "Hvad kan vi hjælpe med?", required: true, rows: 3, "aria-label": "Besked til medarbejder" });
  body.append(
    h("h3", {}, "Eller skriv med en medarbejder"),
    h("form", { onsubmit: async (event) => {
        event.preventDefault();
        const staffId = Number(body.querySelector("input[name=staff]:checked")?.value) || null;
        await run(() => api("/support", { method: "POST", body: { customer_id: state.customerId, staff_id: staffId, text: input.value } }), "Beskeden er sendt");
        openHelp("staff");
      } },
      h("div", { class: "choices", role: "radiogroup", "aria-label": "Vælg medarbejder" },
        h("label", { class: "choice" }, h("input", { type: "radio", name: "staff", value: "", checked: true }),
          h("div", {}, h("div", {}, "Første ledige"), h("div", { class: "sub" }, "Hurtigste svar"))),
        staff.map((s) => h("label", { class: "choice" },
          h("input", { type: "radio", name: "staff", value: s.id }),
          h("span", { class: `dot ${s.online ? "on" : ""}` }),
          h("div", {}, h("div", {}, s.name), h("div", { class: "sub" }, `${s.role} · ${s.online ? "online" : "offline"}`))))),
      input,
      h("button", {}, "Start chat")),
  );
}

function renderCaseChat(body, supportCase) {
  const list = h("div", { class: "chat", "aria-live": "polite" });
  const input = h("input", { placeholder: "Skriv en besked …", "aria-label": "Besked til medarbejder" });
  const draw = (c) => {
    list.replaceChildren(...c.messages.map((m) =>
      chatMessage({ KUNDE: "me", MEDARBEJDER: "staff", SYSTEM: "system" }[m.sender], m.text)));
    if (c.status === "AABEN" && c.messages.at(-1).sender === "KUNDE") list.append(chatMessage("system", "Venter på svar fra en medarbejder …"));
    if (c.status === "LUKKET") list.append(chatMessage("system", "Chatten er afsluttet."));
    list.scrollTop = list.scrollHeight;
  };
  draw(supportCase);
  body.append(list,
    h("form", { class: "composer", onsubmit: async (event) => {
        event.preventDefault();
        if (!input.value.trim()) return;
        draw(await run(() => api(`/support/${supportCase.id}/messages`, { method: "POST", body: { sender: "KUNDE", text: input.value } })));
        input.value = "";
      } }, input, h("button", {}, "Send")));
  // Hent nye svar fra medarbejderen, mens chatten er åben
  state.chatTimer = setInterval(async () => draw(await api(`/support/${supportCase.id}`)), 4000);
}

function stopChatPolling() {
  clearInterval(state.chatTimer);
  state.chatTimer = null;
}

function renderProblem(body) {
  const active = activeReservation();
  if (!active) {
    body.append(
      h("p", {}, "Du kan melde et problem med pladsen, når du har en aktiv reservation."),
      h("button", { class: "secondary", style: "width:100%", onclick: () => openHelp("staff") }, "Kontakt en medarbejder"));
    return;
  }
  body.append(
    h("p", { class: "muted" }, `Plads ${active.spot_label} ved ${active.hotspot_name}`),
    h("div", { class: "big-choice" },
      h("button", { onclick: () => report(active, "PLADS_OPTAGET") },
        h("strong", {}, "Min plads er optaget"), h("span", {}, "Der holder en anden bil. Vi finder en ny plads til dig.")),
      h("button", { onclick: () => report(active, "KAN_IKKE_FINDE") },
        h("strong", {}, "Jeg kan ikke finde pladsen"), h("span", {}, "Få vejvisning, og en medarbejder hjælper dig."))));
}

async function report(r, type) {
  const res = await run(() => api(`/reservations/${r.id}/report`, { method: "POST", body: { type } }));
  await load();
  const title = { MOVED: "Du har fået en ny plads", CANCELLED: "Ingen ledig plads her", HELP: "Hjælp er på vej" }[res.outcome];
  openSheet(title,
    res.outcome === "MOVED" && h("div", { class: "reservation", style: "margin-bottom:10px" },
      h("div", { class: "top", style: "margin:0" },
        h("div", { class: "spot-label" }, h("div", {}, h("small", {}, "PLADS"), res.reservation.spot_label)),
        h("div", { class: "where" }, h("strong", {}, res.reservation.hotspot_name), h("span", {}, "Samme ankomstfrist som før")))),
    h("p", {}, res.message),
    res.outcome === "CANCELLED" && res.alternatives.length && [
      h("h3", {}, "Ledige pladser tæt på"),
      h("ul", { class: "hotspots" }, res.alternatives.map((alt) => h("li", { class: "hotspot" },
        h("div", { class: "text" }, h("div", { class: "name" }, alt.name),
          h("div", { class: "address" }, `${alt.free} ledige · ${formatKm(alt.distance_km)} væk`)),
        h("div", { class: "side" }, h("button", { onclick: () => confirmBooking(alt) }, "Reservér"))))),
    ],
    h("div", { class: "actions" },
      h("button", { class: "secondary", onclick: () => openHelp("staff") }, "Skriv med medarbejder"),
      h("button", { onclick: closeSheet }, "OK")));
}

// ---------------------------------------------------------------- Start
async function start() {
  const [customer, info] = await Promise.all([api(`/customers/${state.customerId}`), api("/info")]);
  Object.assign(state, { customer, info });
  $("#menu-who").textContent = `Logget ind som ${customer.name} · ${customer.car_plate ?? ""}`;
  await load();
  setInterval(() => { if (!$("#sheet").open) load(); }, 15000);   // hold tallene friske
}

start().catch((err) => toast(`Kan ikke hente data fra backenden: ${err.message}`, "error"));
