/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class ScrollButton extends Interaction {
    static selector = ".website_scroll_buttons";
    dynamicContent = {
        _window: {
            "t-on-scroll": this.onScroll,
            "t-on-resize": this.onScroll,
        },
        ".scroll_to_bottom": {
            "t-on-click": this.onClickScrollBottom,
        },
        ".scroll_to_top": {
            "t-on-click": this.onClickScrollTop,
        },
    };

    start() {
        this.topEl = this.el.querySelector(".scroll_icon");
        this.bottomEl = this.el.querySelector(".scroll_icon_bottom");
        this.onScroll();
    }

    _getScrollInfo() {
        const docEl = document.documentElement;
        const body = document.body;
        const wrapwrap = document.getElementById("wrapwrap");

        let scrollTop = window.scrollY || docEl.scrollTop || body.scrollTop || 0;
        let scrollHeight = Math.max(docEl.scrollHeight, body.scrollHeight);
        let clientHeight = window.innerHeight || docEl.clientHeight;

        if (wrapwrap && wrapwrap.scrollHeight > wrapwrap.clientHeight && wrapwrap.scrollTop > 0) {
            scrollTop = wrapwrap.scrollTop;
            scrollHeight = wrapwrap.scrollHeight;
            clientHeight = wrapwrap.clientHeight;
        }

        return { scrollTop, scrollHeight, clientHeight };
    }

    onScroll() {
        const { scrollTop, scrollHeight, clientHeight } = this._getScrollInfo();
        const isScrollable = scrollHeight > clientHeight + 50;

        if (this.topEl) {
            this.topEl.style.display = (isScrollable && scrollTop > 100) ? "block" : "none";
        }

        if (this.bottomEl) {
            const isNearBottom = scrollTop + clientHeight >= scrollHeight - 100;
            this.bottomEl.style.display = (isScrollable && !isNearBottom) ? "block" : "none";
        }
    }

    onClickScrollBottom(ev) {
        ev.preventDefault();
        const wrapwrap = document.getElementById("wrapwrap");
        if (wrapwrap && wrapwrap.scrollHeight > wrapwrap.clientHeight) {
            wrapwrap.scrollTo({ top: wrapwrap.scrollHeight, behavior: "smooth" });
        }
        window.scrollTo({
            top: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight),
            behavior: "smooth",
        });
    }

    onClickScrollTop(ev) {
        ev.preventDefault();
        const wrapwrap = document.getElementById("wrapwrap");
        if (wrapwrap && wrapwrap.scrollHeight > wrapwrap.clientHeight) {
            wrapwrap.scrollTo({ top: 0, behavior: "smooth" });
        }
        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    }
}

registry.category("public.interactions").add("website_scroll_buttons.scroll_button", ScrollButton);
registry.category("public.interactions.edit").add("website_scroll_buttons.scroll_button", {
    Interaction: ScrollButton,
});
