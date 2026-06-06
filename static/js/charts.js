/* ================================================================
   VendorBridge — charts.js
   Chart.js powered analytics for Profile & Reports pages
   Theme-aware: re-renders when light/dark mode is toggled.
   ================================================================ */

(function () {
  "use strict";

  if (typeof Chart === "undefined") return;

  /* ── Get theme-aware colours ─────────────────────────────────── */
  function getColors() {
    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    return {
      green:         isDark ? "#2dda8a"                      : "#1a9e62",
      greenFill:     isDark ? "rgba(45,218,138,0.08)"        : "rgba(26,158,98,0.08)",
      teal:          isDark ? "#22c5a8"                      : "#0fa88d",
      blue:          isDark ? "#5eaaff"                      : "#2271d4",
      purple:        isDark ? "#9b72ff"                      : "#7145e0",
      amber:         isDark ? "#ffbe45"                      : "#c87800",
      red:           isDark ? "#ff5c5c"                      : "#d43030",
      muted:         isDark ? "#6b9077"                      : "#5a7a68",
      grid:          isDark ? "rgba(36,61,46,0.6)"           : "rgba(180,210,195,0.55)",
      gridLine:      isDark ? "rgba(36,61,46,0.5)"           : "rgba(180,210,195,0.5)",
      tooltip_bg:    isDark ? "#132019"                      : "#ffffff",
      tooltip_border:isDark ? "#243d2e"                      : "#cfe0d5",
      tooltip_title: isDark ? "#e8f5ee"                      : "#0d2118",
      tooltip_body:  isDark ? "#6b9077"                      : "#5a7a68",
      centerLabel:   isDark ? "#e8f5ee"                      : "#0d2118",
    };
  }

  /* ── Helpers ─────────────────────────────────────────────────── */
  function gridOpts(C)  { return { color: C.grid, drawBorder: false, drawTicks: false }; }
  function tickOpts(C)  { return { color: C.muted, padding: 8, font: { size: 11 } }; }
  function tooltipCfg(C, extra) {
    return {
      backgroundColor: C.tooltip_bg,
      borderColor:     C.tooltip_border,
      borderWidth:     1,
      titleColor:      C.tooltip_title,
      bodyColor:       C.tooltip_body,
      padding:         12,
      cornerRadius:    8,
      ...(extra || {}),
    };
  }

  /* ── Global defaults ─────────────────────────────────────────── */
  Chart.defaults.font.family = "'Inter', ui-sans-serif, system-ui, sans-serif";
  Chart.defaults.font.size   = 12;
  Chart.defaults.responsive  = true;
  Chart.defaults.maintainAspectRatio = true;

  /* ── Chart registry ──────────────────────────────────────────── */
  const REG = {};
  function destroyAll() {
    Object.keys(REG).forEach((k) => { if (REG[k]) { REG[k].destroy(); delete REG[k]; } });
  }

  /* ── Main build function ─────────────────────────────────────── */
  function buildCharts() {
    destroyAll();
    const C = getColors();

    /* ── CHART 1 — RFQ Status Doughnut ─────────────────────────── */
    const statusEl = document.getElementById("chartRfqStatus");
    if (statusEl) {
      const raw    = JSON.parse(statusEl.dataset.values || "[0,0,0,0,0]");
      const labels = ["Open", "Quoted", "In Approval", "Approved", "Ordered"];
      const colors = [C.blue, C.amber, C.purple, C.green, C.teal];
      const total  = raw.reduce((a, b) => a + b, 0) || 1;

      const centerPlugin = {
        id: "centerText",
        afterDraw(chart) {
          const { ctx: cx, chartArea: { width, height, left, top } } = chart;
          const x = left + width / 2, y = top + height / 2;
          cx.save();
          cx.textAlign = "center"; cx.textBaseline = "middle";
          cx.fillStyle = C.centerLabel; cx.font = "700 28px Inter";
          cx.fillText(total, x, y - 8);
          cx.fillStyle = C.muted; cx.font = "500 11px Inter";
          cx.fillText("Total RFQs", x, y + 12);
          cx.restore();
        },
      };

      REG.chartRfqStatus = new Chart(statusEl, {
        type: "doughnut",
        plugins: [centerPlugin],
        data: {
          labels,
          datasets: [{ data: raw, backgroundColor: colors.map(c => c + "cc"), borderColor: colors, borderWidth: 1.5, hoverBorderWidth: 2.5, hoverOffset: 8 }],
        },
        options: {
          cutout: "68%",
          plugins: {
            legend: { display: false },
            tooltip: tooltipCfg(C, { callbacks: { label(ctx) { const pct = ((ctx.parsed / total) * 100).toFixed(1); return `  ${ctx.label}: ${ctx.parsed} (${pct}%)`; } } }),
          },
          animation: { animateRotate: true, duration: 900, easing: "easeOutQuart" },
        },
      });
    }

    /* ── CHART 2 — Monthly Activity Bar ─────────────────────────── */
    const actEl = document.getElementById("chartActivity");
    if (actEl) {
      const raw    = JSON.parse(actEl.dataset.values || "[0,0,0,0,0,0]");
      const months = JSON.parse(actEl.dataset.labels || '["","","","","",""]');
      const grn    = C.green;

      REG.chartActivity = new Chart(actEl, {
        type: "bar",
        data: {
          labels: months,
          datasets: [{
            label: "Actions", data: raw,
            backgroundColor(ctx) {
              const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.chartArea?.bottom || 200);
              g.addColorStop(0, grn + "cc"); g.addColorStop(1, grn + "15"); return g;
            },
            borderColor: grn, borderWidth: 0, borderRadius: 6, borderSkipped: false, hoverBackgroundColor: grn,
          }],
        },
        options: {
          scales: {
            x: { grid: { display: false }, ticks: tickOpts(C), border: { display: false } },
            y: { grid: gridOpts(C), ticks: { ...tickOpts(C), stepSize: 1 }, border: { display: false }, beginAtZero: true },
          },
          plugins: { legend: { display: false }, tooltip: tooltipCfg(C, { callbacks: { title: (i) => i[0].label, label: (i) => `  Actions: ${i.parsed.y}` } }) },
          animation: { duration: 800, easing: "easeOutQuart" },
        },
      });
    }

    /* ── CHART 3 — PO Spend Line Chart ──────────────────────────── */
    const spendEl = document.getElementById("chartSpend");
    if (spendEl) {
      const raw    = JSON.parse(spendEl.dataset.values || "[0,0,0,0,0,0]");
      const months = JSON.parse(spendEl.dataset.labels || '["","","","","",""]');
      const blu    = C.blue;

      REG.chartSpend = new Chart(spendEl, {
        type: "line",
        data: {
          labels: months,
          datasets: [{
            label: "PO Value (₹)", data: raw,
            borderColor: blu, borderWidth: 2.5,
            pointBackgroundColor: blu, pointBorderColor: "transparent", pointRadius: 5, pointHoverRadius: 8,
            fill: true,
            backgroundColor(ctx) {
              const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 220);
              g.addColorStop(0, blu + "30"); g.addColorStop(1, blu + "00"); return g;
            },
            tension: 0.4,
          }],
        },
        options: {
          scales: {
            x: { grid: { display: false }, ticks: tickOpts(C), border: { display: false } },
            y: { grid: gridOpts(C), ticks: { ...tickOpts(C), callback: (v) => v >= 1000 ? `₹${(v/1000).toFixed(0)}k` : `₹${v}` }, border: { display: false }, beginAtZero: true },
          },
          plugins: { legend: { display: false }, tooltip: tooltipCfg(C, { callbacks: { label: (i) => `  Spend: ₹${Number(i.parsed.y).toLocaleString("en-IN")}` } }) },
          animation: { duration: 900, easing: "easeOutQuart" },
        },
      });
    }

    /* ── CHART 4 — Vendor Radar ──────────────────────────────────── */
    const vendorEl = document.getElementById("chartVendorPerf");
    if (vendorEl) {
      const labels  = JSON.parse(vendorEl.dataset.labels || "[]");
      const ratings = JSON.parse(vendorEl.dataset.values || "[]");

      REG.chartVendorPerf = new Chart(vendorEl, {
        type: "radar",
        data: {
          labels,
          datasets: [{ label: "Rating", data: ratings, backgroundColor: C.greenFill, borderColor: C.green, borderWidth: 2, pointBackgroundColor: C.green, pointBorderColor: "transparent", pointRadius: 5, pointHoverRadius: 8 }],
        },
        options: {
          scales: {
            r: {
              beginAtZero: true, max: 5,
              ticks: { stepSize: 1, color: C.muted, backdropColor: "transparent", font: { size: 10 } },
              grid: { color: C.gridLine }, angleLines: { color: C.gridLine },
              pointLabels: { color: C.muted, font: { size: 11, weight: "600" } },
            },
          },
          plugins: { legend: { display: false }, tooltip: tooltipCfg(C, { callbacks: { label: (i) => `  Rating: ${i.parsed.r} / 5` } }) },
          animation: { duration: 900, easing: "easeOutQuart" },
        },
      });
    }

    /* ── CHART 5 — Procurement Funnel (Horizontal Bar) ───────────── */
    const funnelEl = document.getElementById("chartFunnel");
    if (funnelEl) {
      const raw    = JSON.parse(funnelEl.dataset.values || "[0,0,0,0,0]");
      const labels = ["Open", "Quoted", "In Approval", "Approved", "Ordered"];
      const colors = [C.blue, C.amber, C.purple, C.green, C.teal];

      REG.chartFunnel = new Chart(funnelEl, {
        type: "bar",
        data: {
          labels,
          datasets: [{ label: "RFQs", data: raw, backgroundColor: colors.map(c => c + "bb"), borderColor: colors, borderWidth: 1.5, borderRadius: 6, borderSkipped: false }],
        },
        options: {
          indexAxis: "y",
          scales: {
            x: { grid: gridOpts(C), ticks: tickOpts(C), border: { display: false }, beginAtZero: true },
            y: { grid: { display: false }, ticks: { ...tickOpts(C), font: { size: 12, weight: "600" } }, border: { display: false } },
          },
          plugins: { legend: { display: false }, tooltip: tooltipCfg(C, { callbacks: { label: (i) => `  ${i.parsed.x} RFQs` } }) },
          animation: { duration: 900, easing: "easeOutQuart" },
        },
      });
    }

    /* ── CHART 6 — Polar Area (Reports page) ─────────────────────── */
    const polarEl = document.getElementById("chartPolar");
    if (polarEl) {
      const labels = JSON.parse(polarEl.dataset.labels || "[]");
      const values = JSON.parse(polarEl.dataset.values || "[]");
      const colors = [C.green, C.blue, C.purple, C.amber, C.teal, C.red];

      REG.chartPolar = new Chart(polarEl, {
        type: "polarArea",
        data: {
          labels,
          datasets: [{ data: values, backgroundColor: colors.slice(0, labels.length).map(c => c + "55"), borderColor: colors.slice(0, labels.length), borderWidth: 1.5 }],
        },
        options: {
          scales: {
            r: { ticks: { color: C.muted, backdropColor: "transparent", font: { size: 10 } }, grid: { color: C.gridLine } },
          },
          plugins: {
            legend: { position: "bottom", labels: { color: C.muted, boxWidth: 10, padding: 12, font: { size: 11 } } },
            tooltip: tooltipCfg(C),
          },
          animation: { duration: 900 },
        },
      });
    }
  }

  /* ── Initial render ──────────────────────────────────────────── */
  buildCharts();

  /* ── Re-render on theme change (dispatched by app.js) ────────── */
  document.addEventListener("themechange", () => {
    // Small delay to let CSS vars update
    setTimeout(buildCharts, 60);
  });

  /* ── Number Counter animation ────────────────────────────────── */
  function animateCount(el, target, duration) {
    duration = duration || 1000;
    const start = performance.now();
    const isDecimal = String(target).includes(".");
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      el.textContent = isDecimal ? current.toFixed(1) : Math.floor(current).toLocaleString("en-IN");
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  document.querySelectorAll(".count-up[data-value]").forEach((el) => {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { animateCount(el, parseFloat(el.dataset.value)); obs.disconnect(); }
      });
    }, { threshold: 0.3 });
    obs.observe(el);
  });

  /* ── Sidebar mobile toggle ───────────────────────────────────── */
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }

})();
