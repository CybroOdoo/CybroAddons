import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class CollectionSnippet extends Interaction {
    static selector = ".ref-collection--container";

    dynamicContent = {
        ".ref-collection__item": { "t-on-click": this.onItemClick },
    };

    start() {
        this.el.querySelector(".ref-collection__item")?.classList.add("selected");
    }

    onItemClick(ev) {
        this.el
            .querySelectorAll(".ref-collection__item")
            .forEach((item) => item.classList.remove("selected"));
        ev.currentTarget.classList.add("selected");
    }
}

registry
    .category("public.interactions")
    .add("theme_eco_refine.collection_snippet", CollectionSnippet);