/** Header scroll state and the footer back to top link. */

import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/** The floating pill of the header gets more solid once the page is scrolled. */
export class AqHeader extends Interaction {
    static selector = "header#top";
    dynamicContent = {
        _window: { "t-on-scroll.noUpdate": this.onScroll },
    };

    setup() {
        this.registerCleanup(() => this.el.classList.remove("is-scrolled"));
    }

    start() {
        this.onScroll();
    }

    onScroll() {
        this.el.classList.toggle("is-scrolled", window.scrollY > 24);
    }
}

/** Back to top link of the footer scrolls smoothly instead of jumping. */
export class AqToTop extends Interaction {
    static selector = ".aq-to-top";
    dynamicContent = {
        _root: { "t-on-click.prevent": this.onClick },
    };

    onClick() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

const category = registry.category("public.interactions");
category.add("theme_aquere.header", AqHeader);
category.add("theme_aquere.to_top", AqToTop);
