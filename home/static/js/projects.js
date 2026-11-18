document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".project-card");
  if (!cards.length) return;

  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

  // 1) reveal on scroll
  const io = new IntersectionObserver((entries) => {
    entries.forEach(en => {
      if (en.isIntersecting) {
        en.target.classList.add("is-in", "wow-float");
        io.unobserve(en.target);
      }
    });
  }, { threshold: 0.16 });

  cards.forEach(card => {
    card.classList.add("wow-reveal");
    io.observe(card);

    // добавляем слой блика, если его нет
    if (!card.querySelector(".wow-glare")) {
      const glare = document.createElement("div");
      glare.className = "wow-glare";
      card.appendChild(glare);
    }

    let raf = null;

    const onMove = (e) => {
      if (raf) cancelAnimationFrame(raf);

      raf = requestAnimationFrame(() => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;   // 0..1
        const y = (e.clientY - r.top) / r.height;   // 0..1

        // tilt
        const rx = clamp((0.5 - y) * 10, -10, 10);
        const ry = clamp((x - 0.5) * 12, -12, 12);

        // лёгкий “подъём” + tilt
        card.style.transform =
          `translateY(-4px) rotateX(${rx}deg) rotateY(${ry}deg)`;

        // позиция подсветки
        const mx = (x * 100).toFixed(2) + "%";
        const my = (y * 100).toFixed(2) + "%";
        card.style.setProperty("--mx", mx);
        card.style.setProperty("--my", my);
        card.style.setProperty("--mx2", (100 - x * 100).toFixed(2) + "%");
        card.style.setProperty("--my2", (100 - y * 100).toFixed(2) + "%");

        // позиция блика (чуть смещаем)
        card.style.setProperty("--gx", ((x * 120) - 60).toFixed(2) + "%");
        card.style.setProperty("--gy", ((y * 120) - 60).toFixed(2) + "%");
      });
    };

    const onEnter = () => {
      card.classList.add("is-hover");
      card.classList.remove("wow-float");
    };

    const onLeave = () => {
      if (raf) cancelAnimationFrame(raf);
      card.classList.remove("is-hover");
      card.classList.add("wow-float");
      card.style.transform = "";
      card.style.removeProperty("--mx");
      card.style.removeProperty("--my");
      card.style.removeProperty("--mx2");
      card.style.removeProperty("--my2");
      card.style.removeProperty("--gx");
      card.style.removeProperty("--gy");
    };

    // pointer-events лучше mousemove, чтобы работало с тачпадами ровнее
    card.addEventListener("pointerenter", onEnter);
    card.addEventListener("pointermove", onMove);
    card.addEventListener("pointerleave", onLeave);
  });
});


