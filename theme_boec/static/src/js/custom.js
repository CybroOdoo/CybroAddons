/** @odoo-module **/

function initializeBanner(carousel) {
    if (carousel.dataset.boecInitialized) {
        return;
    }
    carousel.dataset.boecInitialized = "true";
    const slides = [...carousel.children];
    if (!slides.length) {
        return;
    }

    let activeIndex = 0;
    const showSlide = (index) => {
        activeIndex = (index + slides.length) % slides.length;
        slides.forEach((slide, slideIndex) => {
            slide.classList.toggle("boec-carousel-active", slideIndex === activeIndex);
        });
        dots.forEach((dot, dotIndex) => dot.classList.toggle("active", dotIndex === activeIndex));
    };

    const nav = document.createElement("div");
    nav.className = "owl-nav";
    const previous = document.createElement("button");
    previous.type = "button";
    previous.className = "owl-prev";
    previous.setAttribute("aria-label", "Previous slide");
    previous.innerHTML = '<span class="pre">&#10094;</span>';
    const next = document.createElement("button");
    next.type = "button";
    next.className = "owl-next";
    next.setAttribute("aria-label", "Next slide");
    next.innerHTML = '<span class="nxt">&#10095;</span>';
    previous.addEventListener("click", () => showSlide(activeIndex - 1));
    next.addEventListener("click", () => showSlide(activeIndex + 1));
    nav.append(previous, next);

    const dots = slides.map((_, index) => {
        const dot = document.createElement("button");
        dot.type = "button";
        dot.className = "owl-dot";
        dot.setAttribute("aria-label", `Show slide ${index + 1}`);
        dot.innerHTML = `<span>${index + 1}</span>`;
        dot.addEventListener("click", () => showSlide(index));
        return dot;
    });
    const dotsContainer = document.createElement("div");
    dotsContainer.className = "owl-dots";
    dotsContainer.append(...dots);
    carousel.append(nav, dotsContainer);
    carousel.classList.add("owl-loaded");
    showSlide(0);
}

function initializeQuantityInputs() {
    document.querySelectorAll(".quantity").forEach((quantity) => {
        if (quantity.dataset.boecInitialized) {
            return;
        }
        const input = quantity.querySelector('input[type="number"]');
        if (!input) {
            return;
        }
        quantity.dataset.boecInitialized = "true";
        const navigation = document.createElement("div");
        navigation.className = "quantity-nav";
        const addButton = (label, delta) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = `quantity-button quantity-${delta > 0 ? "up" : "down"}`;
            button.textContent = label;
            button.addEventListener("click", () => {
                const current = Number(input.value) || 0;
                const min = input.min === "" ? -Infinity : Number(input.min);
                const max = input.max === "" ? Infinity : Number(input.max);
                input.value = Math.min(max, Math.max(min, current + delta));
                input.dispatchEvent(new Event("change", { bubbles: true }));
            });
            navigation.append(button);
        };
        addButton("+", 1);
        addButton("-", -1);
        input.after(navigation);
    });
}

function initializeTheme() {
    window.setTimeout(() => document.body.classList.add("loaded"), 1000);
    document.querySelectorAll(".banner .owl-carousel").forEach(initializeBanner);
    document.querySelectorAll(".banner_added").forEach((banner) => banner.classList.add("banner_hide"));
    document.querySelectorAll("ul.navbar-nav a").forEach((link) => {
        link.parentElement?.classList.toggle("active", link.href === window.location.href);
    });
    document.querySelectorAll("#myDIV .nav-link, #myDIV .btn").forEach((button) => {
        button.addEventListener("click", () => button.classList.add("active"));
    });
    document.querySelectorAll(".card-header").forEach((header) => {
        header.addEventListener("click", () => {
            const icon = header.querySelector("i");
            icon?.classList.toggle("fa-angle-down");
            icon?.classList.toggle("fa-angle-up");
        });
    });
    initializeQuantityInputs();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeTheme, { once: true });
} else {
    initializeTheme();
}
