/* YugKrit - notifications.js: notification bell dropdown behavior */

document.addEventListener("DOMContentLoaded", function () {
  const bell = document.getElementById("notif-bell");
  const menu = document.getElementById("notif-menu");
  if (!bell || !menu) return;

  bell.addEventListener("click", () => {
    menu.classList.toggle("open");
  });
});
