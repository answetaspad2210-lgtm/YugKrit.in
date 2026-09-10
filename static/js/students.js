/* YugKrit - students.js: student directory search + skill add form */

document.addEventListener("DOMContentLoaded", function () {
  const skillForm = document.getElementById("add-skill-form");
  if (skillForm) {
    skillForm.addEventListener("submit", (e) => {
      const input = skillForm.querySelector("input[name=skill_name]");
      if (!input.value.trim()) {
        e.preventDefault();
        input.reportValidity();
      }
    });
  }
});
