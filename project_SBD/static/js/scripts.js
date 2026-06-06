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

  const initGalleryForms = () => {
    document.querySelectorAll("[data-gallery-mode-options]").forEach((options) => {
      const form = options.closest("form");
      const singleUpload = form?.querySelector("[data-gallery-single-upload]");
      const multipleUpload = form?.querySelector("[data-gallery-multiple-upload]");
      const singleInput = form?.querySelector("[data-gallery-single-input]");
      const multipleInput = form?.querySelector("[data-gallery-multiple-input]");
      const selectedFiles = form?.querySelector("[data-gallery-selected-files]");
      const existingGallery = form?.querySelector("[data-existing-gallery]");
      if (!singleInput || !multipleInput) return;

      const updateMode = () => {
        const mode = options.querySelector('input[name="image_mode"]:checked')?.value || "single";
        const multiple = mode === "multiple";
        singleUpload.style.display = multiple ? "none" : "";
        multipleUpload.style.display = multiple ? "" : "none";
        singleInput.disabled = multiple;
        multipleInput.disabled = !multiple;
        if (existingGallery) {
          existingGallery.classList.toggle("gallery-form-muted", !multiple);
        }
      };

      options.addEventListener("change", updateMode);
      multipleInput.addEventListener("change", () => {
        const files = [...multipleInput.files];
        if (!selectedFiles) return;
        selectedFiles.hidden = files.length === 0;
        if (files.length) {
          const names = files.map((file) => file.name).join(", ");
          selectedFiles.textContent = `Đã chọn ${files.length} ảnh: ${names}`;
        } else {
          selectedFiles.textContent = "";
        }
      });
      form.querySelectorAll('input[name="cover_image"]').forEach((coverInput) => {
        coverInput.addEventListener("change", () => {
          if (!coverInput.checked || !coverInput.value.startsWith("gallery:")) return;
          const imageId = coverInput.value.split(":")[1];
          const deleteInput = form.querySelector(
            `input[name="delete_gallery_images"][value="${imageId}"]`
          );
          if (deleteInput) deleteInput.checked = false;
        });
      });
      form.querySelectorAll('input[name="delete_gallery_images"]').forEach((deleteInput) => {
        deleteInput.addEventListener("change", () => {
          if (!deleteInput.checked) return;
          const selectedCover = form.querySelector(
            `input[name="cover_image"][value="gallery:${deleteInput.value}"]`
          );
          if (selectedCover?.checked) {
            form.querySelector('input[name="cover_image"][value="primary"]')?.click();
          }
        });
      });
      updateMode();
    });
  };

  const initContentGalleries = () => {
    document.querySelectorAll("[data-content-gallery]").forEach((gallery) => {
      const slides = [...gallery.querySelectorAll("[data-gallery-slide]")];
      const thumbs = [...gallery.querySelectorAll("[data-gallery-index]")];
      const lightbox = gallery.nextElementSibling;
      if (!slides.length || !lightbox?.matches("[data-gallery-lightbox]")) return;

      const lightboxImage = lightbox.querySelector("[data-lightbox-image]");
      const viewport = lightbox.querySelector("[data-lightbox-viewport]");
      const zoomLabel = lightbox.querySelector("[data-lightbox-zoom-label]");
      let activeIndex = Math.max(0, slides.findIndex((slide) => slide.classList.contains("is-active")));
      let scale = 1;
      let translateX = 0;
      let translateY = 0;
      let dragging = false;
      let pointerX = 0;
      let pointerY = 0;

      const renderTransform = () => {
        lightboxImage.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
        lightboxImage.classList.toggle("is-zoomed", scale > 1);
        if (zoomLabel) zoomLabel.textContent = `${Math.round(scale * 100)}%`;
      };

      const resetZoom = () => {
        scale = 1;
        translateX = 0;
        translateY = 0;
        renderTransform();
      };

      const setZoom = (nextScale) => {
        scale = Math.min(5, Math.max(0.5, nextScale));
        if (scale <= 1) {
          translateX = 0;
          translateY = 0;
        }
        renderTransform();
      };

      const show = (index) => {
        activeIndex = (index + slides.length) % slides.length;
        slides.forEach((slide, slideIndex) => {
          slide.classList.toggle("is-active", slideIndex === activeIndex);
        });
        thumbs.forEach((thumb, thumbIndex) => {
          thumb.classList.toggle("is-active", thumbIndex === activeIndex);
        });
        if (!lightbox.hidden) {
          lightboxImage.src = slides[activeIndex].dataset.gallerySrc;
          resetZoom();
        }
      };

      const openLightbox = (index) => {
        show(index);
        lightboxImage.src = slides[activeIndex].dataset.gallerySrc;
        resetZoom();
        lightbox.hidden = false;
        document.body.classList.add("gallery-lightbox-open");
        lightbox.querySelector("[data-lightbox-close]")?.focus();
      };

      const closeLightbox = () => {
        lightbox.hidden = true;
        lightboxImage.src = "";
        document.body.classList.remove("gallery-lightbox-open");
      };

      gallery.querySelector("[data-gallery-prev]")?.addEventListener("click", () => show(activeIndex - 1));
      gallery.querySelector("[data-gallery-next]")?.addEventListener("click", () => show(activeIndex + 1));
      lightbox.querySelector("[data-lightbox-prev]")?.addEventListener("click", () => show(activeIndex - 1));
      lightbox.querySelector("[data-lightbox-next]")?.addEventListener("click", () => show(activeIndex + 1));
      lightbox.querySelector("[data-lightbox-close]")?.addEventListener("click", closeLightbox);
      lightbox.querySelector("[data-lightbox-zoom-in]")?.addEventListener("click", () => setZoom(scale + 0.25));
      lightbox.querySelector("[data-lightbox-zoom-out]")?.addEventListener("click", () => setZoom(scale - 0.25));
      lightbox.querySelector("[data-lightbox-reset]")?.addEventListener("click", resetZoom);
      lightbox.querySelector("[data-lightbox-fullscreen]")?.addEventListener("click", () => {
        if (document.fullscreenElement) {
          document.exitFullscreen?.();
        } else {
          lightbox.requestFullscreen?.();
        }
      });

      viewport?.addEventListener("wheel", (event) => {
        event.preventDefault();
        setZoom(scale + (event.deltaY < 0 ? 0.2 : -0.2));
      }, { passive: false });
      viewport?.addEventListener("dblclick", () => {
        if (scale > 1) resetZoom();
        else setZoom(2);
      });
      viewport?.addEventListener("pointerdown", (event) => {
        if (scale <= 1) return;
        dragging = true;
        pointerX = event.clientX;
        pointerY = event.clientY;
        viewport.setPointerCapture(event.pointerId);
      });
      viewport?.addEventListener("pointermove", (event) => {
        if (!dragging) return;
        translateX += event.clientX - pointerX;
        translateY += event.clientY - pointerY;
        pointerX = event.clientX;
        pointerY = event.clientY;
        renderTransform();
      });
      viewport?.addEventListener("pointerup", () => {
        dragging = false;
      });
      viewport?.addEventListener("pointercancel", () => {
        dragging = false;
      });

      slides.forEach((slide, index) => {
        slide.addEventListener("click", () => openLightbox(index));
      });
      thumbs.forEach((thumb) => {
        thumb.addEventListener("click", () => show(Number(thumb.dataset.galleryIndex)));
      });

      lightbox.addEventListener("click", (event) => {
        if (event.target === lightbox) closeLightbox();
      });
      document.addEventListener("keydown", (event) => {
        if (lightbox.hidden) return;
        if (event.key === "Escape") closeLightbox();
        if (event.key === "ArrowLeft") show(activeIndex - 1);
        if (event.key === "ArrowRight") show(activeIndex + 1);
      });

      if (slides.length < 2) {
        gallery.querySelectorAll("[data-gallery-prev], [data-gallery-next]").forEach((button) => {
          button.hidden = true;
        });
        lightbox.querySelectorAll("[data-lightbox-prev], [data-lightbox-next]").forEach((button) => {
          button.hidden = true;
        });
      }
      show(activeIndex);
    });
  };

  const ready = () => {
    initWow();
    initStickyNavbar();
    initOffcanvasCloseOnClick();
    initGalleryForms();
    initContentGalleries();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();
