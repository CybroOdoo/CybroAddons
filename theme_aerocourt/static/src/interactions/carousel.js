/** Testimonials carousel with dots, arrows and autoplay. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AcInteraction } from "./base";
import { pad } from "./utils";

/** Testimonials carousel: arrows (in the section header), dots, keyboard and swipe. */
export class AcTestimonialCarousel extends AcInteraction {
    static selector = ".ac-testimonials";
    dynamicContent = {
        "#testimonialCarousel": { "t-on-keydown": this.onKeyDown },
        "#testiPrev": { "t-on-click": () => this.go(this.index - 1) },
        "#testiNext": { "t-on-click": () => this.go(this.index + 1) },
        "#testiDots": { "t-on-click": this.onDotClick },
        "#testiTrack": {
            "t-on-pointerdown": (ev) => (this.startX = ev.clientX),
            "t-on-pointerup": this.onPointerUp,
            "t-on-pointercancel": () => (this.startX = null),
            "t-att-style": () => ({ "--index": this.index }),
        },
        ".ac-testimonial": {
            "t-att-aria-hidden": (el) => String(this.slides.indexOf(el) !== this.index),
            "t-att-inert": (el) => this.slides.indexOf(el) !== this.index,
            "t-att-aria-label": (el) =>
                _t("%(current)s of %(total)s", {
                    current: this.slides.indexOf(el) + 1,
                    total: this.slides.length,
                }),
        },
        ".ac-carousel__dot": {
            "t-att-aria-current": (el) => String(Number(el.dataset.index) === this.index),
        },
        "#testiCount": {
            "t-out": () => `${pad(this.index + 1)} / ${pad(this.slides.length)}`,
        },
    };

    setup() {
        this.track = this.el.querySelector("#testiTrack");
        this.slides = Array.from(this.track.querySelectorAll(".ac-testimonial"));
        this.index = 0;
        this.startX = null;
    }

    willStart() {
        // Rendered before the dynamic content is bound, so the dots are part of it
        this.setHTML(
            this.el.querySelector("#testiDots"),
            this.slides
                .map(
                    (_slide, i) =>
                        `<button type="button" class="ac-carousel__dot" aria-label="${_t("Show testimonial %s", i + 1)}" data-index="${i}"></button>`
                )
                .join("")
        );
    }

    go(i) {
        this.index = (i + this.slides.length) % this.slides.length;
    }

    onDotClick(ev) {
        const dot = ev.target.closest("[data-index]");
        if (dot) {
            this.go(Number(dot.dataset.index));
        }
    }

    onKeyDown(ev) {
        if (ev.key === "ArrowLeft") {
            this.go(this.index - 1);
        } else if (ev.key === "ArrowRight") {
            this.go(this.index + 1);
        }
    }

    onPointerUp(ev) {
        if (this.startX === null) {
            return;
        }
        const dx = ev.clientX - this.startX;
        if (Math.abs(dx) > 50) {
            this.go(this.index + (dx < 0 ? 1 : -1));
        }
        this.startX = null;
    }
}

registry.category("public.interactions").add("theme_aerocourt.testimonial_carousel", AcTestimonialCarousel);
