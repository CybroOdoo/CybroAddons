/** Entrance animations of the design: fade-up reveal, scroll-lit manifesto words and parallax backgrounds. */

import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Fade the `.aq-reveal` elements in as they scroll into view. The page flags
 * itself with `aq-js` so the hidden start state only exists when scripts run
 * (and is taken away again in the website editor).
 */
export class AqReveal extends Interaction {
    static selector = "#wrapwrap";

    setup() {
        const root = document.documentElement;
        root.classList.add("aq-js");
        this.revealed = [];
        this.registerCleanup(() => {
            root.classList.remove("aq-js");
            this.revealed.forEach((el) => el.classList.remove("is-visible"));
        });
    }

    start() {
        const items = this.el.querySelectorAll(".aq-reveal");
        if (!("IntersectionObserver" in window) || reduceMotion()) {
            items.forEach((el) => el.classList.add("is-visible"));
            return;
        }
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (!entry.isIntersecting) {
                        continue;
                    }
                    entry.target.classList.add("is-visible");
                    this.revealed.push(entry.target);
                    observer.unobserve(entry.target);
                }
            },
            { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
        );
        items.forEach((el) => observer.observe(el));
        this.registerCleanup(() => observer.disconnect());
    }
}

/** Manifesto statement: its words light up as it scrolls into view. */
export class AqManifesto extends Interaction {
    static selector = ".aq-manifesto-text";

    setup() {
        const original = this.el.innerHTML;
        this.registerCleanup(() => (this.el.innerHTML = original));
        const words = this.el.textContent.trim().split(/\s+/);
        this.el.replaceChildren();
        this.words = words.map((word, i) => {
            const span = document.createElement("span");
            span.className = "aq-w";
            span.textContent = word;
            this.el.append(span, i < words.length - 1 ? " " : "");
            return span;
        });
    }

    start() {
        this.addListener(window, "scroll", () => this.schedule(), { passive: true });
        this.update();
    }

    schedule() {
        if (this.ticking) {
            return;
        }
        this.ticking = true;
        requestAnimationFrame(() => {
            this.ticking = false;
            this.update();
        });
    }

    update() {
        const rect = this.el.getBoundingClientRect();
        const vh = window.innerHeight;
        const progress = reduceMotion() ? 1 : (vh * 0.85 - rect.top) / (rect.height + vh * 0.35);
        const lit = Math.round(Math.max(0, Math.min(1, progress)) * this.words.length);
        this.words.forEach((el, i) => el.classList.toggle("is-lit", i < lit));
    }
}

/** Gentle parallax of the cinematic background of the process band. */
export class AqParallax extends Interaction {
    static selector = ".aq-source-bg";

    start() {
        if (reduceMotion()) {
            return;
        }
        this.addListener(window, "scroll", () => this.schedule(), { passive: true });
        this.registerCleanup(() => (this.el.style.transform = ""));
        this.update();
    }

    schedule() {
        if (this.ticking) {
            return;
        }
        this.ticking = true;
        requestAnimationFrame(() => {
            this.ticking = false;
            this.update();
        });
    }

    update() {
        const vh = window.innerHeight;
        const rect = this.el.parentElement.getBoundingClientRect();
        if (rect.bottom < 0 || rect.top > vh) {
            return;
        }
        const progress = (rect.top + rect.height / 2 - vh / 2) / (vh + rect.height);
        this.el.style.transform = `translate3d(0, ${(progress * -18).toFixed(2)}%, 0)`;
    }
}

const category = registry.category("public.interactions");
category.add("theme_aquere.reveal", AqReveal);
category.add("theme_aquere.manifesto", AqManifesto);
category.add("theme_aquere.parallax", AqParallax);
