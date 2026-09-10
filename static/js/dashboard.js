/* YugKrit - dashboard.js: shared dashboard interactivity */

document.addEventListener("DOMContentLoaded", function () {
  initSearchFilter();
});

/* Live client-side filter for simple search boxes with data-search-target */
function initSearchFilter() {
  document.querySelectorAll("[data-search-input]").forEach((input) => {
    const targetSelector = input.getAttribute("data-search-input");
    const rows = document.querySelectorAll(targetSelector);
    input.addEventListener("input", () => {
      const term = input.value.toLowerCase();
      rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? "" : "none";
      });
    });
  });
}
