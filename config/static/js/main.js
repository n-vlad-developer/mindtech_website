document.addEventListener("DOMContentLoaded", () => {
  const yearSpan = document.getElementById("year");
  if (yearSpan) yearSpan.textContent = new Date().getFullYear();

  // бургер меню
  const burgerBtn = document.getElementById("burgerBtn");
  const nav = document.querySelector(".nav");
  if (burgerBtn && nav) {
    burgerBtn.addEventListener("click", () => nav.classList.toggle("open"));
    nav.querySelectorAll("a").forEach(a =>
      a.addEventListener("click", () => nav.classList.remove("open"))
    );
  }

  // язык: только ссылки + запомнить выбор (БЕЗ редиректов)
  const langSwitch = document.getElementById("langSwitch");
  if (langSwitch) {
    langSwitch.addEventListener("click", (e) => {
      const a = e.target.closest("a.lang-btn");
      if (!a) return;
      const lang = (a.dataset.lang === "en") ? "en" : "ru";
      localStorage.setItem("mt_lang", lang);
    });
  }

  // reveal
  const revealElements = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealElements.length) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("reveal-visible");
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealElements.forEach(el => observer.observe(el));
  } else {
    revealElements.forEach(el => el.classList.add("reveal-visible"));
  }

  // ===== PRELOADER (нормальный старт анимации + шапку не показываем) =====
  const preloader = document.getElementById("preloader");
  if (preloader) {
    const key = "mt_preloader_seen_v2"; // поменяли версию, чтобы обновление точно применилось
    const alreadySeen = sessionStorage.getItem(key) === "1";
    const preloaderOff = document.documentElement.classList.contains("preloader-off");

    // прячем шапку пока прелоадер активен
    document.documentElement.classList.add("preloader-active");

    if (alreadySeen || preloaderOff) {
      preloader.classList.add("hidden");
      preloader.classList.remove("play");
      document.body.classList.remove("no-scroll");
      document.documentElement.classList.remove("preloader-active");
    } else {
      document.body.classList.add("no-scroll");
      sessionStorage.setItem(key, "1");

      // запуск анимации строго со следующего кадра, чтобы не было “логотип сразу стоит”
      requestAnimationFrame(() => {
        preloader.classList.add("play");
      });

      // держим прелоадер фиксированное время (как у тебя было)
      setTimeout(() => {
        preloader.classList.add("hidden");
        document.body.classList.remove("no-scroll");
        document.documentElement.classList.add("preloader-off");
        document.documentElement.classList.remove("preloader-active");
      }, 2800);
    }
  }
});
