/* YugKrit - auth.js: multi-step registration wizard */

document.addEventListener("DOMContentLoaded", function () {
  const wizard = document.querySelector("[data-wizard]");
  if (!wizard) return;

  const steps = Array.from(wizard.querySelectorAll(".form-step"));
  const stepperItems = Array.from(wizard.querySelectorAll(".stepper-step"));
  const nextButtons = wizard.querySelectorAll("[data-wizard-next]");
  const prevButtons = wizard.querySelectorAll("[data-wizard-prev]");
  let current = 0;

  function render() {
    steps.forEach((s, i) => s.classList.toggle("active", i === current));
    stepperItems.forEach((s, i) => {
      s.classList.toggle("active", i === current);
      s.classList.toggle("complete", i < current);
    });
  }

  function validateCurrentStep() {
    const activeStep = steps[current];
    const requiredFields = activeStep.querySelectorAll("[required]");
    for (const field of requiredFields) {
      if (!field.value || !field.value.trim()) {
        field.reportValidity();
        return false;
      }
    }
    return true;
  }

  nextButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (!validateCurrentStep()) return;
      if (current < steps.length - 1) {
        current += 1;
        render();
        window.scrollTo({ top: wizard.offsetTop - 20, behavior: "smooth" });
      }
    });
  });

  prevButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (current > 0) {
        current -= 1;
        render();
      }
    });
  });

  render();
});

/* File upload widget with progress-style UI (client-side preview only;
   actual upload happens on normal form submit). */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-file-drop]").forEach((drop) => {
    const inputId = drop.getAttribute("data-file-drop");
    const input = document.getElementById(inputId);
    const listId = drop.getAttribute("data-file-list");
    const list = listId ? document.getElementById(listId) : null;
    if (!input) return;

    drop.addEventListener("click", () => input.click());
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("dragover"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("dragover"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      drop.classList.remove("dragover");
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        renderFiles();
      }
    });
    input.addEventListener("change", renderFiles);

    function renderFiles() {
      if (!list) return;
      list.innerHTML = "";
      Array.from(input.files).forEach((file) => {
        const item = document.createElement("div");
        item.className = "file-item";
        const sizeKb = (file.size / 1024).toFixed(1);
        item.innerHTML = `<span><i class="fa-solid fa-file"></i> ${file.name} (${sizeKb} KB)</span>`;
        list.appendChild(item);
      });
    }
  });
});

/* Universal "confirm password" validation — any <input data-match="other-field-id">
   is checked against the referenced field's value before its form submits.
   Used on every registration form (University, ULB/NGO, Student, Citizen). */
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input[data-match]").forEach((confirmField) => {
    const targetId = confirmField.getAttribute("data-match");
    const originalField = document.getElementById(targetId);
    if (!originalField) return;

    function checkMatch() {
      if (confirmField.value && originalField.value !== confirmField.value) {
        confirmField.setCustomValidity("Passwords do not match.");
      } else {
        confirmField.setCustomValidity("");
      }
    }
    confirmField.addEventListener("input", checkMatch);
    originalField.addEventListener("input", checkMatch);

    const form = confirmField.closest("form");
    if (form) {
      form.addEventListener("submit", (e) => {
        checkMatch();
        if (!confirmField.checkValidity()) {
          e.preventDefault();
          confirmField.reportValidity();
        }
      });
    }
  });
});
