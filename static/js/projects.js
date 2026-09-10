/* YugKrit - projects.js: team builder + milestone interactions */

document.addEventListener("DOMContentLoaded", function () {
  initTeamBuilder();
  initMilestoneForms();
});

function initTeamBuilder() {
  const container = document.getElementById("team-members-container");
  const addBtn = document.getElementById("add-member-btn");
  if (!container || !addBtn) return;

  const roles = ["Team Leader", "Developer", "Researcher", "Designer", "Data Analyst", "Field Coordinator", "Other"];

  function rowTemplate() {
    const roleOptions = roles.map((r) => `<option value="${r}">${r}</option>`).join("");
    const row = document.createElement("div");
    row.className = "card";
    row.style.marginBottom = "12px";
    row.innerHTML = `
      <div class="card-body" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:10px;align-items:end;">
        <div class="form-group" style="margin-bottom:0">
          <label>Full Name</label>
          <input type="text" name="member_name[]" placeholder="Student name" required>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>College Email</label>
          <input type="email" name="member_email[]" placeholder="student@college.edu" required>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>Registration No.</label>
          <input type="text" name="member_regno[]" placeholder="ABC2026CS102" required>
        </div>
        <div class="form-group" style="margin-bottom:0">
          <label>Role</label>
          <select name="member_role[]">${roleOptions}</select>
        </div>
        <button type="button" class="btn btn-outline btn-icon remove-member-btn" title="Remove">
          <i class="fa-solid fa-trash"></i>
        </button>
      </div>`;
    row.querySelector(".remove-member-btn").addEventListener("click", () => row.remove());
    return row;
  }

  addBtn.addEventListener("click", () => container.appendChild(rowTemplate()));

  // Start with one row pre-filled
  if (container.children.length === 0) container.appendChild(rowTemplate());
}

function initMilestoneForms() {
  document.querySelectorAll("[data-milestone-status-form]").forEach((form) => {
    const select = form.querySelector("select[name=status]");
    if (!select) return;
    select.addEventListener("change", () => {
      const commentField = form.querySelector("textarea[name=comment]");
      if (select.value === "CHANGES_REQUESTED" && commentField) {
        commentField.setAttribute("required", "required");
      } else if (commentField) {
        commentField.removeAttribute("required");
      }
    });
  });
}
