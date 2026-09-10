/* YugKrit - maps.js: Leaflet + OpenStreetMap helpers */

document.addEventListener("DOMContentLoaded", function () {
  initChallengeMap();
  initLocationPicker();
});

/* Government / marketplace map showing multiple challenge markers.
   Expects: <div id="challenge-map" data-locations='[{"id":1,"title":"...", "lat":..,"lng":..,"category":"..","priority":80,"status":"VERIFIED"}]'></div> */
function initChallengeMap() {
  const el = document.getElementById("challenge-map");
  if (!el || typeof L === "undefined") return;

  let locations = [];
  try {
    locations = JSON.parse(el.getAttribute("data-locations") || "[]");
  } catch (e) {
    locations = [];
  }

  const state = el.getAttribute("data-state") || "";
  const stateCenters = { Punjab: [30.9010, 75.8573], Jharkhand: [23.3441, 85.3096], "Uttar Pradesh": [26.8467, 80.9462] };
  const center = locations.length ? [locations[0].lat, locations[0].lng] : (stateCenters[state] || [23.5, 80.5]);
  const map = L.map(el).setView(center, locations.length ? 7 : 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18,
  }).addTo(map);

  locations.forEach((loc) => {
    if (!loc.lat || !loc.lng) return;
    const marker = L.marker([loc.lat, loc.lng]).addTo(map);
    const priorityColor = loc.priority >= 70 ? "#c0392b" : loc.priority >= 40 ? "#b8860b" : "#1c8a54";
    marker.bindPopup(`
      <h4>${loc.title}</h4>
      <p style="margin:2px 0;font-size:12px;">${loc.category || ""}</p>
      <p style="margin:2px 0;font-size:12px;">Priority: <b style="color:${priorityColor}">${loc.priority || "-"}</b> &middot; ${loc.status || ""}</p>
      ${loc.url ? `<a href="${loc.url}" style="font-size:12px;">View Challenge &rarr;</a>` : ""}
    `);
  });
}

/* Single-pin picker for the "submit challenge" location step.
   Expects: <div id="location-picker"></div>, and hidden inputs #latitude / #longitude */
function initLocationPicker() {
  const el = document.getElementById("location-picker");
  if (!el || typeof L === "undefined") return;

  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");

  const stateField = document.querySelector("[name='state']");
  const stateCenters = { Punjab: [30.9010, 75.8573], Jharkhand: [23.3441, 85.3096], "Uttar Pradesh": [26.8467, 80.9462] };
  const defaultCenter = stateCenters[stateField?.value] || stateCenters.Jharkhand;
  const map = L.map(el).setView(defaultCenter, 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18,
  }).addTo(map);

  let marker = L.marker(defaultCenter, { draggable: true }).addTo(map);
  setCoords(defaultCenter[0], defaultCenter[1]);

  marker.on("dragend", () => {
    const pos = marker.getLatLng();
    setCoords(pos.lat, pos.lng);
  });

  map.on("click", (e) => {
    marker.setLatLng(e.latlng);
    setCoords(e.latlng.lat, e.latlng.lng);
  });

  stateField?.addEventListener("change", () => {
    const center = stateCenters[stateField.value];
    if (!center) return;
    map.setView(center, 8);
    marker.setLatLng(center);
    setCoords(center[0], center[1]);
  });

  document.addEventListener("yugkrit:location", (event) => {
    const { lat, lng } = event.detail;
    marker.setLatLng([lat, lng]);
    map.setView([lat, lng], 15);
    setCoords(lat, lng);
  });

  function setCoords(lat, lng) {
    if (latInput) latInput.value = lat.toFixed(6);
    if (lngInput) lngInput.value = lng.toFixed(6);
  }
}
