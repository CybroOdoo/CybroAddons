import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class RefurbAboutUs extends Interaction {
    static selector = ".ref-wrapper";

    dynamicContent = {
        ".ref-abt-button": { "t-on-click": this.toggleDiv },
        ".ref-mob-btn": { "t-on-click": this.toggleContent },
        ".custom-nav_prev": { "t-on-click": () => this.carousel("prev") },
        ".custom-nav_next": { "t-on-click": () => this.carousel("next") },
    };

    start() {
        const defaultIndex = 2;
        const defaultContent = this.el.querySelector(
            `.ref-abt_mob .ref-mob-btn:nth-child(${defaultIndex + 1}) .ref-abt-button__mobcontent`
        );
        defaultContent?.classList.add("show");

        const buttons = this.el.querySelectorAll(".ref-abt-button");
        buttons[1]?.classList.add("active");
        buttons[3]?.classList.add("active");

        // owlCarousel is a jQuery plugin, so it still needs the global jQuery
        window.$(this.el).find(".owl-carousel-abt").owlCarousel({
            loop: true,
            margin: 10,
            nav: false,
            autoplay: true,
            responsive: {
                0: { items: 2 },
                600: { items: 3 },
                1000: { items: 5 },
            },
        });
    }

    destroy() {
        window.$(this.el).find(".owl-carousel-abt").trigger("destroy.owl.carousel");
    }

    carousel(direction) {
        window.$(this.el).find(".owl-carousel-abt").trigger(`${direction}.owl.carousel`);
    }

    toggleDiv(ev) {
        if (!ev.target.classList.contains("ref-abt-button")) {
            return;
        }
        const about = ev.target.querySelector(".ref-abt-button__content");
        this.el.querySelectorAll(".ref-abt-button").forEach((btn) => {
            btn.classList.remove("active");
            const content = btn.querySelector(".ref-abt-button__content");
            if (content) {
                content.style.display = "none";
            }
        });
        ev.target.classList.add("active");
        about.style.display = "block";
    }

    toggleContent(ev) {
        const target = ev.target;
        let index = 4;
        for (let i = 0; i < 4; i++) {
            if (target.classList.contains(`div${i}`)) {
                index = i;
                break;
            }
        }
        this.el.querySelectorAll(".ref-abt-button__mobcontent").forEach((el, i) => {
            el.classList.toggle("show", i === index);
        });
        this.el.querySelectorAll(".button-mob-text").forEach((el, i) => {
            if (i === index) {
                el.classList.toggle("hidden");
            } else {
                el.classList.remove("hidden");
            }
        });
    }
}

registry
    .category("public.interactions")
    .add("theme_eco_refine.about_us", RefurbAboutUs);