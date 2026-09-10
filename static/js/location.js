/* YugKrit - permission-based location autofill for address forms. */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form").forEach((form) => {
    const fieldNames = ["city", "district", "state"];
    const fields = fieldNames.map((name) => form.querySelector(`[name='${name}']`));
    const latitude = form.querySelector("[name='latitude']");
    const longitude = form.querySelector("[name='longitude']");
    if (!fields.some(Boolean) && !latitude && !longitude) return;

    const action = document.createElement("div");
    action.className = "location-autofill";
    action.innerHTML = '<button type="button" class="btn btn-outline btn-sm"><i class="fa-solid fa-location-crosshairs"></i> Use my location</button><span role="status"></span>';
    const anchor = fields.find(Boolean)?.closest(".form-group") || form.querySelector("#location-picker")?.parentElement;
    if (anchor) anchor.parentElement.insertBefore(action, anchor);

    const button = action.querySelector("button");
    const status = action.querySelector("span");
    const requestLocation = () => {
      if (!navigator.geolocation) {
        status.textContent = "Location is not supported by this browser.";
        return;
      }
      if (!window.isSecureContext) {
        status.textContent = "Location needs HTTPS. Open the secure YugKrit URL.";
        return;
      }
      button.disabled = true;
      status.textContent = "Asking for location permission...";
      navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude: lat, longitude: lng } = position.coords;
        if (latitude) latitude.value = lat.toFixed(6);
        if (longitude) longitude.value = lng.toFixed(6);
        document.dispatchEvent(new CustomEvent("yugkrit:location", { detail: { lat, lng } }));
        status.textContent = "Location found. Filling address...";
        try {
          const response = await fetch(`/api/location/reverse?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`);
          if (!response.ok) throw new Error("Reverse lookup failed");
          const payload = await response.json();
          const values = payload.data || {};
          fields.forEach((field, index) => {
            const value = values[fieldNames[index]];
            if (field && value) field.value = value;
          });
          const addressField = form.querySelector("[name='address']");
          if (addressField && !addressField.value) addressField.value = [values.city, values.district, values.state].filter(Boolean).join(", ");
          status.textContent = "Location filled. Please review it before continuing.";
        } catch (error) {
          status.textContent = "Location detected.";
        } finally {
          button.disabled = false;
        }
      }, () => {
        status.textContent = "Location permission was denied. You can enter the address manually.";
        button.disabled = false;
      }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 });
    };

    button.addEventListener("click", requestLocation);

    // Ask as soon as the form opens; the button remains available if the browser blocks it.
    window.setTimeout(requestLocation, 300);
  });
});