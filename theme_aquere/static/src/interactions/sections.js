/** Interactive sections of the design: collection showcase, accordions, testimonials, value panels, process tracker and form counter. */

import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const pad = (n) => String(n).padStart(2, "0");
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Collection: hover or tap a product to bring it to the stage. */
export class AqShowcase extends Interaction {
    static selector = ".aq-showcase";

    start() {
        this.items = [...this.el.querySelectorAll(".aq-sc-item")];
        this.slides = [...this.el.querySelectorAll(".aq-stage-slide")];
        this.counter = this.el.querySelector(".aq-stage-current");
        const initial = Math.max(0, this.items.findIndex((i) => i.classList.contains("is-active")));
        const counterText = this.counter?.textContent;
        this.registerCleanup(() => {
            this.set(initial);
            if (this.counter) {
                this.counter.textContent = counterText;
            }
        });
        const canHover = window.matchMedia("(hover: hover)").matches;
        this.items.forEach((item, i) => {
            this.addListener(item.querySelector(".aq-sc-head"), "click", () => this.set(i));
            if (canHover) {
                this.addListener(item, "mouseenter", () => this.set(i));
            }
        });
    }

    set(index) {
        this.items.forEach((item, i) => {
            item.classList.toggle("is-active", i === index);
            item.querySelector(".aq-sc-head").setAttribute("aria-expanded", String(i === index));
        });
        this.slides.forEach((slide, i) => slide.classList.toggle("is-active", i === index));
        if (this.counter) {
            this.counter.textContent = pad(index + 1);
        }
    }
}

/** Accordion (responsibility, FAQ): one answer open at a time. */
export class AqAccordion extends Interaction {
    static selector = ".aq-accordion";

    start() {
        this.items = [...this.el.querySelectorAll(".aq-acc-item")];
        const initial = this.items.map((item) => item.classList.contains("is-open"));
        this.registerCleanup(() =>
            this.items.forEach((item, i) => this.toggle(item, initial[i]))
        );
        this.items.forEach((item) => {
            this.addListener(item.querySelector(".aq-acc-head"), "click", () => {
                const open = !item.classList.contains("is-open");
                this.items.forEach((other) => this.toggle(other, false));
                this.toggle(item, open);
            });
        });
    }

    toggle(item, open) {
        item.classList.toggle("is-open", open);
        item.querySelector(".aq-acc-head").setAttribute("aria-expanded", String(open));
    }
}

/** Testimonials: arrows, counter and an autoplay progress bar. */
export class AqTestimonials extends Interaction {
    static selector = ".aq-testimonials";

    start() {
        this.slides = [...this.el.querySelectorAll(".aq-t-slide")];
        if (!this.slides.length) {
            return;
        }
        this.current = this.el.querySelector(".aq-t-current");
        this.total = this.el.querySelector(".aq-t-count");
        this.bar = this.el.querySelector(".aq-t-progress span");
        this.index = Math.max(0, this.slides.findIndex((s) => s.classList.contains("is-active")));
        const initial = this.index;
        const currentText = this.current?.textContent;
        this.registerCleanup(() => {
            this.slides.forEach((s, i) => s.classList.toggle("is-active", i === initial));
            this.bar?.classList.remove("is-running");
            if (this.current) {
                this.current.textContent = currentText;
            }
        });
        this.el.querySelectorAll(".aq-t-btn").forEach((btn) =>
            this.addListener(btn, "click", () => this.show(this.index + Number(btn.dataset.dir)))
        );
        if (this.bar && !reduceMotion()) {
            this.addListener(this.bar, "animationend", () => this.show(this.index + 1));
            this.restartBar();
        }
    }

    show(index) {
        this.index = (index + this.slides.length) % this.slides.length;
        this.slides.forEach((s, i) => s.classList.toggle("is-active", i === this.index));
        if (this.current) {
            this.current.textContent = pad(this.index + 1);
        }
        this.restartBar();
    }

    restartBar() {
        if (!this.bar || reduceMotion()) {
            return;
        }
        this.bar.classList.remove("is-running");
        void this.bar.offsetWidth;
        this.bar.classList.add("is-running");
    }
}

/** Story page: value panels expand on hover, focus or tap. */
export class AqValuePanels extends Interaction {
    static selector = ".aq-value-panels";

    start() {
        this.panels = [...this.el.querySelectorAll(".aq-vp")];
        const initial = this.panels.map((p) => p.classList.contains("is-open"));
        this.registerCleanup(() =>
            this.panels.forEach((p, i) => p.classList.toggle("is-open", initial[i]))
        );
        for (const panel of this.panels) {
            for (const type of ["mouseenter", "focus", "click"]) {
                this.addListener(panel, type, () => this.open(panel));
            }
        }
    }

    open(panel) {
        this.panels.forEach((p) => p.classList.toggle("is-open", p === panel));
    }
}

/** Process page: the sticky tracker follows the stage in view. */
export class AqProcessTracker extends Interaction {
    static selector = ".aq-stages-grid";

    start() {
        const tracker = this.el.querySelector(".aq-stage-tracker");
        this.stages = [...this.el.querySelectorAll(".aq-stage")];
        if (!tracker || !this.stages.length || !("IntersectionObserver" in window)) {
            return;
        }
        const no = tracker.querySelector(".aq-tracker-current");
        const name = tracker.querySelector(".aq-tracker-name");
        const bar = tracker.querySelector(".aq-tracker-bar span");
        const original = [no.textContent, name.textContent, bar.style.width];
        this.registerCleanup(() => {
            [no.textContent, name.textContent, bar.style.width] = original;
            this.stages.forEach((s) => s.classList.remove("is-current"));
        });
        const observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (!entry.isIntersecting) {
                        continue;
                    }
                    const i = this.stages.indexOf(entry.target);
                    this.stages.forEach((s, j) => s.classList.toggle("is-current", i === j));
                    no.textContent = pad(i + 1);
                    name.textContent = entry.target.dataset.name;
                    bar.style.width = `${((i + 1) / this.stages.length) * 100}%`;
                }
            },
            { rootMargin: "-45% 0px -45% 0px" }
        );
        this.stages.forEach((s) => observer.observe(s));
        this.registerCleanup(() => observer.disconnect());
    }
}

/** Contact form: live character counter of the message. */
export class AqCharCount extends Interaction {
    static selector = ".aq-f-message";
    dynamicContent = {
        textarea: { "t-on-input.noUpdate": this.update },
    };

    start() {
        this.update();
    }

    update() {
        const area = this.el.querySelector("textarea");
        const counter = this.el.querySelector(".aq-char-count");
        if (area && counter) {
            counter.textContent = `${area.value.length} / ${area.maxLength}`;
        }
    }
}

const category = registry.category("public.interactions");
category.add("theme_aquere.showcase", AqShowcase);
category.add("theme_aquere.accordion", AqAccordion);
category.add("theme_aquere.testimonials", AqTestimonials);
category.add("theme_aquere.value_panels", AqValuePanels);
category.add("theme_aquere.process_tracker", AqProcessTracker);
category.add("theme_aquere.char_count", AqCharCount);
