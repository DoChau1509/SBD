(() => {
  const initWow = () => {
    if (!window.WOW) return;
    try {
      new window.WOW({ mobile: true, live: false }).init();
    } catch {
      // ignore
    }
  };

  const initStickyNavbar = () => {
    const navbar = document.querySelector(".site-navbar");
    if (!navbar) return;
    const onScroll = () => {
      navbar.classList.toggle("scrolled", window.scrollY > 10);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  };

  const initOffcanvasCloseOnClick = () => {
    const offcanvasEl = document.getElementById("mobileNav");
    if (!offcanvasEl || !window.bootstrap) return;
    offcanvasEl.addEventListener("click", (e) => {
      const link = e.target.closest("a");
      if (!link) return;
      const instance = window.bootstrap.Offcanvas.getInstance(offcanvasEl);
      if (instance) instance.hide();
    });
  };

  const ready = () => {
    initWow();
    initStickyNavbar();
    initOffcanvasCloseOnClick();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();

