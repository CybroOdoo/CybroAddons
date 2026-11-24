/** Motion effects: reveal on scroll, counters, timeline and parallax. */

import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { configValue, prefersReducedMotion } from "./utils";

const canObserve = () => !prefersReducedMotion() && "IntersectionObserver" in window;

/** Entrance animation: the element appears when it scrolls into view. */
export class AcReveal extends Interaction {
    static selector = "[data-reveal], [data-reveal-stagger]";

    setup() {
        const el = this.el;
        this.stagger = el.hasAttribute("data-reveal-stagger");
        // Take the attributes back when the interaction stops (website editor)
        const attributes = ["data-reveal", "data-reveal-stagger"].map((name) => [
            name,
            el.getAttribute(name),
        ]);
        this.registerCleanup(() => {
            for (const [name, value] of attributes) {
                if (value !== null) {
                    el.setAttribute(name, value);
                }
            }
            el.classList.remove("is-visible");
        });
    }

    start() {
        if (this.stagger) {
            Array.from(this.el.children).forEach((child, i) => child.style.setProperty("--i", i));
        }
        if (!canObserve()) {
            this.handBack();
            return;
        }
        // A fully clipped element never reports as intersecting: clip reveals watch their parent
        const node = this.el.dataset.reveal === "clip" ? this.el.parentElement : this.el;
        this.observer = new IntersectionObserver(
            (entries) => {
                if (!entries.some((entry) => entry.isIntersecting)) {
                    return;
                }
                this.observer.disconnect();
                this.el.classList.add("is-visible");
                const extra = this.stagger ? this.el.children.length * 90 : 0;
                this.waitForTimeout(() => this.handBack(), 1400 + extra);
            },
            { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
        );
        this.observer.observe(node);
        this.registerCleanup(() => this.observer.disconnect());
    }

    /** Gives control back to the component styles (hover transforms, transitions). */
    handBack() {
        this.el.removeAttribute("data-reveal");
        this.el.removeAttribute("data-reveal-stagger");
        this.el.classList.remove("is-visible");
    }
}

/**
 * Numbers that count up when they come into view. The number to reach is the
 * text of the element (so it is edited in the website builder like any text),
 * or the club setting named by `data-ac`. The text is restored when stopped.
 */
export class AcCounter extends Interaction {
    static selector = "[data-count]";

    start() {
        const original = this.el.textContent;
        this.registerCleanup(() => (this.el.textContent = original));
        const written = Number(original.replace(/[^\d.]/g, ""));
        this.target = Number(configValue(this.el.dataset.ac) ?? (written || this.el.dataset.count));
        if (!canObserve()) {
            this.format(this.target);
            return;
        }
        this.format(0);
        this.observer = new IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => entry.isIntersecting)) {
                    this.observer.disconnect();
                    this.animate();
                }
            },
            { threshold: 0.6 }
        );
        this.observer.observe(this.el);
        this.registerCleanup(() => this.observer.disconnect());
    }

    format(value) {
        const padTo = Number(this.el.dataset.pad || 0);
        this.el.textContent = padTo ? String(value).padStart(padTo, "0") : value.toLocaleString("en-US");
    }

    animate() {
        const duration = 1600;
        const start = performance.now();
        const tick = (now) => {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(2, -10 * p); // expo out
            this.format(Math.round(this.target * (p === 1 ? 1 : eased)));
            if (p < 1) {
                this.waitForAnimationFrame(() => tick(performance.now()));
            }
        };
        this.waitForAnimationFrame(() => tick(performance.now()));
    }
}

/** About page timeline: draws the line, then each milestone in order. */
export class AcTimeline extends Interaction {
    static selector = "[data-timeline]";

    start() {
        this.el
            .querySelectorAll(".ac-timeline__item")
            .forEach((item, i) => item.style.setProperty("--i", i));
        this.registerCleanup(() => this.el.classList.remove("is-drawn"));
        if (!canObserve()) {
            this.el.classList.add("is-drawn");
            return;
        }
        this.observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    this.el.classList.add("is-drawn");
                    this.observer.disconnect();
                }
            },
            { threshold: 0.25 }
        );
        this.observer.observe(this.el);
        this.registerCleanup(() => this.observer.disconnect());
    }
}

/** Slow vertical drift of the hero background and of the framed photographs. */
export class AcParallax extends Interaction {
    static selector = "[data-parallax-hero], [data-parallax]";
    dynamicContent = {
        _window: {
            "t-on-scroll.noUpdate": this.throttled(this.update),
            "t-on-resize.noUpdate": this.throttled(this.update),
        },
    };

    setup() {
        this.isHero = this.el.hasAttribute("data-parallax-hero");
        this.enabled = !prefersReducedMotion();
        this.registerCleanup(() => {
            this.el.style.transform = "";
        });
    }

    start() {
        if (this.enabled) {
            this.update();
        }
    }

    update() {
        if (!this.enabled) {
            return;
        }
        const rect = this.el.parentElement.getBoundingClientRect();
        if (this.isHero) {
            const p = Math.min(1, Math.max(0, -rect.top / Math.max(rect.height, 1)));
            this.el.style.transform = `translate3d(0, ${(p * 22).toFixed(2)}%, 0)`;
        } else {
            const vh = window.innerHeight;
            const p = Math.min(1, Math.max(0, (vh - rect.top) / (vh + rect.height)));
            this.el.style.transform = `translate3d(0, ${(-6 + p * 12).toFixed(2)}%, 0)`;
        }
    }
}

const category = registry.category("public.interactions");
category.add("theme_aerocourt.reveal", AcReveal);
category.add("theme_aerocourt.counter", AcCounter);
category.add("theme_aerocourt.timeline", AcTimeline);
category.add("theme_aerocourt.parallax", AcParallax);
