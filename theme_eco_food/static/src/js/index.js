import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

class EcoFoodStickyHeader extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        _root: { "t-on-scroll": this.updateHeader },
    };

    start() {
        this.topbar = this.el.querySelector(".topbar");
        this.headerOffset = this.topbar?.offsetTop || 0;
        this.registerCleanup(() => {
            this.topbar?.classList.remove("fadeInDown", "topbar_margin");
        });
        this.updateHeader();
    }

    updateHeader() {
        const sticky = this.el.scrollTop >= Math.max(this.headerOffset, 100);
        this.topbar?.classList.toggle("fadeInDown", sticky);
        this.topbar?.classList.toggle("topbar_margin", sticky);
    }
}

registry.category("public.interactions").add("theme_eco_food.sticky_header", EcoFoodStickyHeader);
