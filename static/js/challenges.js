/* YugKrit - challenges.js: challenge marketplace / list filter interactions */

document.addEventListener("DOMContentLoaded", function () {
  const filterForm = document.querySelector("[data-filter-form]");
  if (filterForm) {
    filterForm.querySelectorAll("select").forEach((select) => {
      select.addEventListener("change", () => filterForm.submit());
    });
  }

  // Save (bookmark) button toggle - purely client-side visual state for now
  document.querySelectorAll("[data-save-challenge]").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.classList.toggle("btn-accent");
      btn.classList.toggle("btn-outline");
      const icon = btn.querySelector("i");
      if (icon) icon.classList.toggle("fa-solid");
      if (icon) icon.classList.toggle("fa-regular");
      showToast(btn.classList.contains("btn-accent") ? "Saved to your list" : "Removed from saved", "info");
    });
  });
});
