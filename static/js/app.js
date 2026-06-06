/* ================================================================
   VendorBridge ERP — app.js
   Core interactivity, helpers, and count-up animations
   ================================================================ */

(function () {
  "use strict";

  /* ── Quotation price estimator ─────────────────────────────── */
  document.addEventListener("input", (event) => {
    const form = event.target.closest(".quotation-form");
    if (!form || !event.target.name.includes("unit_prices")) return;
    const prices = event.target.value.split(/\n+/).map((v) => Number(v.trim() || 0));
    const estimate = prices.reduce((sum, p) => sum + p, 0);
    const box = form.querySelector(".total-box");
    if (box)
      box.textContent = `Estimated unit-price sum: ₹${estimate.toLocaleString("en-IN")}. Final total uses RFQ quantities + GST after save.`;
  });

  /* ── Restore filter select value from URL ──────────────────── */
  document.querySelectorAll("select[name='status']").forEach((select) => {
    const selected = new URLSearchParams(window.location.search).get("status");
    if (selected) select.value = selected;
  });

  /* ── Auto-dismiss messages ─────────────────────────────────── */
  document.querySelectorAll(".message").forEach((msg) => {
    setTimeout(() => {
      msg.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      msg.style.opacity = "0";
      msg.style.transform = "translateY(-8px)";
      setTimeout(() => msg.remove(), 500);
    }, 4500);
  });

  /* ── Card hover glow effect ────────────────────────────────── */
  document.querySelectorAll(".card, .quote-card, .stat").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty("--mouse-x", `${x}%`);
      card.style.setProperty("--mouse-y", `${y}%`);
    });
  });

  /* ── Table row click highlight ─────────────────────────────── */
  document.querySelectorAll("tbody tr").forEach((row) => {
    row.addEventListener("click", () => {
      document.querySelectorAll("tbody tr.selected").forEach((r) => r.classList.remove("selected"));
      row.classList.add("selected");
    });
  });

  /* ── Number count-up animation ─────────────────────────────── */
  function animateCount(el, target, duration) {
    if (typeof target !== "number" || isNaN(target)) return;
    const start = performance.now();
    const isDecimal = String(target).includes(".");
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = target * eased;
      el.textContent = isDecimal
        ? current.toFixed(1)
        : Math.floor(current).toLocaleString("en-IN");
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* ── IntersectionObserver for count-up ─────────────────────── */
  const countEls = document.querySelectorAll(".count-up[data-value]");
  if (countEls.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const el = entry.target;
            const raw = el.dataset.value;
            const target = parseFloat(String(raw).replace(/,/g, ""));
            if (!isNaN(target)) animateCount(el, target, 900);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.4 }
    );
    countEls.forEach((el) => observer.observe(el));
  }

  /* ── Sidebar active link highlight on scroll ───────────────── */
  const navLinks = document.querySelectorAll("nav a");

  /* ── Animate stats grid cards on load ─────────────────────── */
  document.querySelectorAll(".stats-grid .stat").forEach((el, i) => {
    el.style.animationDelay = `${i * 60}ms`;
    el.classList.add("animate-fade-up");
  });

  /* ── Chart panels fade up on scroll ───────────────────────── */
  const panels = document.querySelectorAll(".chart-panel, .panel, .card");
  if ("IntersectionObserver" in window) {
    const panelObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
            panelObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    panels.forEach((panel) => {
      panel.style.opacity = "0";
      panel.style.transform = "translateY(20px)";
      panel.style.transition = "opacity 0.5s ease, transform 0.5s ease";
      panelObserver.observe(panel);
    });
  }

  /* ── Smooth table search (client-side) ─────────────────────── */
  const searchInput = document.getElementById("vendorSearch");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const q = searchInput.value.toLowerCase();
      document.querySelectorAll("tbody tr").forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? "" : "none";
      });
    });
  }

  /* ── Tooltip for badges ─────────────────────────────────────── */
  const badgeDescriptions = {
    open: "Collecting vendor quotations",
    quoted: "Quotations received, ready for comparison",
    approval: "Waiting for manager approval",
    approved: "Approved and cleared for PO",
    ordered: "Purchase order generated",
    pending: "Awaiting action",
    rejected: "Request rejected",
    active: "Active and operational",
    blocked: "Blocked from participating",
    draft: "Draft — not yet submitted",
    submitted: "Submitted and under review",
    selected: "Selected as the winning quote",
    issued: "Purchase order issued",
    completed: "Fully completed",
    sent: "Invoice sent to vendor",
    paid: "Payment received",
    overdue: "Payment overdue — action required",
  };

  document.querySelectorAll(".badge").forEach((badge) => {
    const key = badge.textContent.trim().toLowerCase();
    if (badgeDescriptions[key]) {
      badge.title = badgeDescriptions[key];
      badge.style.cursor = "help";
    }
  });


  /* ── Theme Toggle ─────────────────────────────────────────────── */
  (function initTheme() {
    const html = document.documentElement;
    const btn = document.getElementById("themeToggle");
    const iconDark = document.getElementById("themeIconDark");
    const iconLight = document.getElementById("themeIconLight");

    // Load saved preference (default: light)
    const saved = localStorage.getItem("vb-theme") || "light";
    html.setAttribute("data-theme", saved);

    function applyTheme(theme) {
      html.setAttribute("data-theme", theme);
      localStorage.setItem("vb-theme", theme);
      if (iconDark) iconDark.style.display = (theme === "dark") ? "" : "none";
      if (iconLight) iconLight.style.display = (theme === "light") ? "" : "none";
      // Notify charts to re-render with right colors
      document.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
    }

    // Initialize icons
    applyTheme(saved);

    if (btn) {
      btn.addEventListener("click", () => {
        const current = html.getAttribute("data-theme") || "light";
        applyTheme(current === "light" ? "dark" : "light");
      });
    }
  })();

  console.log("✅ VendorBridge app.js loaded");
})();
