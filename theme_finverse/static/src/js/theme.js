import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/** Header: mobile drawer + sticky navbar */
export class FinverseMobileMenu extends Interaction {
    static selector = ".header-container";
    dynamicContent = {
        "#hamburgerMenu": { "t-on-click.stop": this.toggle },
        "#mobileCloseBtn": { "t-on-click": this.close },
        "#mobileMenuBackdrop": { "t-on-click": this.close },
        ".mobile-menu .nav-item a, .mobile-nav-actions a": { "t-on-click": this.close },
        "_document": { "t-on-keydown": this.onKeydown },
        "_window": {
            "t-on-scroll.withTarget": this.updateSticky,
            "t-on-resize": this.onResize,
        },
    };

    setup() {
        this.hamburger = this.el.querySelector("#hamburgerMenu");
        this.menu = this.el.querySelector("#mobileMenu");
        this.navbar = this.el.querySelector("#finance-navbar");
    }

    start() {
        this.updateSticky();
    }

    get isOpen() {
        return !!this.menu && this.menu.classList.contains("active");
    }

    open() {
        this.hamburger?.classList.add("active");
        this.menu?.classList.add("active");
        this.hamburger?.setAttribute("aria-expanded", "true");
        document.body.classList.add("mobile-open");
    }

    close() {
        this.hamburger?.classList.remove("active");
        this.menu?.classList.remove("active");
        this.hamburger?.setAttribute("aria-expanded", "false");
        document.body.classList.remove("mobile-open");
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    onKeydown(ev) {
        if (ev.key === "Escape" && this.isOpen) {
            this.close();
        }
    }

    onResize() {
        if (window.innerWidth > 1024 && this.isOpen) {
            this.close();
        }
    }

    updateSticky() {
        const top = window.scrollY || document.documentElement.scrollTop;
        this.navbar?.classList.toggle("sticky", top >= 10);
    }

    destroy() {
        document.body.classList.remove("mobile-open");
    }
}

/** Scroll-to-top, reveal animation, smooth anchors, demo contact form */
export class FinverseInteractions extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        "#scrollToTop": { "t-on-click": this.scrollTop },
        "_window": { "t-on-scroll": this.onScroll },
        "a[href^='#']": { "t-on-click": this.onAnchorClick },
        "#contactForm": { "t-on-submit.prevent": this.onContactSubmit },
        ".service-card": {
            "t-on-mouseenter": (ev) => (ev.currentTarget.style.transform = "translateY(-8px)"),
            "t-on-mouseleave": (ev) => (ev.currentTarget.style.transform = "translateY(0)"),
        },
    };

    setup() {
        this.observer = new IntersectionObserver(
            (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add("animate-in")),
            { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
        );
    }

    start() {
        this.el.querySelectorAll("section").forEach((s) => this.observer.observe(s));
    }

    destroy() {
        this.observer.disconnect();
    }

    onScroll() {
        const btn = this.el.querySelector("#scrollToTop");
        btn?.classList.toggle("visible", window.scrollY > 300);
    }

    scrollTop() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    onAnchorClick(ev) {
        const id = ev.currentTarget.getAttribute("href");
        if (id && id !== "#") {
            const target = document.querySelector(id);
            if (target) {
                ev.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        }
    }

    onContactSubmit() {
        const btn = this.el.querySelector("#submitBtn");
        const text = this.el.querySelector("#btnText");
        const loader = this.el.querySelector("#btnLoader");
        const form = this.el.querySelector("#contactForm");
        if (!btn) {
            return;
        }
        btn.disabled = true;
        if (text) text.textContent = "Sending...";
        if (loader) loader.style.display = "block";
        this.waitForTimeout(() => {
            if (text) text.textContent = "Message Sent!";
            if (loader) loader.style.display = "none";
            form.reset();
            this.waitForTimeout(() => {
                btn.disabled = false;
                if (text) text.textContent = "Send Message";
            }, 3000);
        }, 2000);
    }
}

/** FAQ accordion */
export class FinverseFAQ extends Interaction {
    static selector = ".finance-faq";
    dynamicContent = {
        ".faq-question": { "t-on-click": this.onQuestionClick },
    };

    onQuestionClick(ev) {
        const clicked = ev.currentTarget.closest(".faq-item");
        const wasActive = clicked.classList.contains("active");
        this.el.querySelectorAll(".faq-item").forEach((item) => this.setState(item, false));
        if (!wasActive) {
            this.setState(clicked, true);
        }
    }

    setState(item, active) {
        item.classList.toggle("active", active);
        const answer = item.querySelector(".faq-answer");
        const icon = item.querySelector("iconify-icon");
        if (answer) answer.style.display = active ? "block" : "none";
        if (icon) icon.setAttribute("icon", active ? "lucide:chevron-up" : "lucide:chevron-down");
    }
}

registry.category("public.interactions").add("theme_finverse.mobile_menu", FinverseMobileMenu);
registry.category("public.interactions").add("theme_finverse.interactions", FinverseInteractions);
registry.category("public.interactions").add("theme_finverse.faq", FinverseFAQ);
