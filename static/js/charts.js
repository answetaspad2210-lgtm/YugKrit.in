/* YugKrit - charts.js: thin wrapper around Chart.js so templates only need
   to declare a <canvas data-chart='{"type":"bar", ...}'> element. */

document.addEventListener("DOMContentLoaded", function () {
  if (typeof Chart === "undefined") return;

  document.querySelectorAll("canvas[data-chart]").forEach((canvas) => {
    try {
      const config = JSON.parse(canvas.getAttribute("data-chart"));
      const palette = ["#0f5c4a", "#d9822b", "#1e5b9e", "#c0392b", "#b8860b", "#6b7c76", "#1c8a54"];

      if (config.dataset && Array.isArray(config.dataset.data)) {
        config.dataset.backgroundColor = config.dataset.data.map((_, i) => palette[i % palette.length]);
      }

      new Chart(canvas.getContext("2d"), {
        type: config.type || "bar",
        data: {
          labels: config.labels || [],
          datasets: [
            Object.assign(
              {
                label: config.label || "",
                data: (config.dataset && config.dataset.data) || config.data || [],
                borderRadius: 6,
                borderWidth: config.type === "line" ? 2 : 0,
                tension: 0.35,
                fill: config.type === "line" ? false : true,
                backgroundColor: (config.dataset && config.dataset.backgroundColor) || "#0f5c4a",
                borderColor: "#0f5c4a",
              },
              config.datasetOverrides || {}
            ),
          ],
        },
        options: Object.assign(
          {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: config.showLegend !== false && config.type === "doughnut" } },
            scales: config.type === "doughnut" ? {} : {
              y: { beginAtZero: true, grid: { color: "#eef3f1" } },
              x: { grid: { display: false } },
            },
          },
          config.optionsOverrides || {}
        ),
      });
    } catch (err) {
      console.error("Chart render failed", err);
    }
  });
});
