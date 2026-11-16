import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class RefurbProductTabs extends Interaction {
    static selector = ".tab";

    dynamicContent = {
        ".tab-link": { "t-on-click": this.openTab },
    };

    openTab(ev) {
        const link = ev.currentTarget;
        const tabId = link.classList.contains("tab1") ? "tab1" : "tab2";
        const container = this.el.parentNode;

        container.querySelectorAll(".tab-content").forEach((el) => {
            el.style.display = "none";
        });
        this.el.querySelectorAll(".tab-link").forEach((el) => {
            el.classList.remove("active");
        });

        const content = container.querySelector(`#${tabId}`);
        if (content) {
            content.style.display = "block";
        }
        link.classList.add("active");
    }
}

registry
    .category("public.interactions")
    .add("theme_eco_refine.product_tabs", RefurbProductTabs);