import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class MenuOverflow extends Interaction {
    static selector = "header#top .top_menu";

    start() {
        this.onResize = () => {
            window.cancelAnimationFrame(this.refreshId);
            this.refreshId = window.requestAnimationFrame(() => this.adapt());
        };
        const fontsReady = document.fonts ? document.fonts.ready : Promise.resolve();
        fontsReady.then(() => this.adapt());
        window.addEventListener("resize", this.onResize);
        this.resizeObserver = new ResizeObserver(this.onResize);
        this.resizeObserver.observe(this.el.parentElement);
        this.resizeObserver.observe(this.el);
    }

    destroy() {
        window.removeEventListener("resize", this.onResize);
        window.cancelAnimationFrame(this.refreshId);
        this.resizeObserver?.disconnect();
    }

    adapt() {
        this.restore();
        if (window.matchMedia("(max-width: 991px)").matches) {
            return;
        }
        const items = [...this.el.children];
        let menuWidth = items.reduce((width, item) => width + this.outerWidth(item), 0);
        const availableWidth = this.el.clientWidth || this.el.parentElement.clientWidth;
        if (availableWidth - menuWidth >= -0.1) {
            return;
        }
        const dropdownMenu = this.addOverflowButton();
        menuWidth += this.outerWidth(this.overflowToggle);
        while (availableWidth - menuWidth < -0.1 && items.length) {
            const item = items.pop();
            menuWidth -= this.outerWidth(item);
            item.classList.remove("nav-item");
            const link = item.querySelector(".nav-link");
            if (link) {
                link.classList.replace("nav-link", "dropdown-item");
            }
            dropdownMenu.prepend(item);
        }
    }

    restore() {
        if (!this.overflowToggle) {
            return;
        }
        const dropdownMenu = this.overflowToggle.querySelector(".dropdown-menu");
        for (const item of [...dropdownMenu.children]) {
            item.classList.add("nav-item");
            item.querySelector(".dropdown-item")?.classList.replace("dropdown-item", "nav-link");
            this.el.insertBefore(item, this.overflowToggle);
        }
        this.overflowToggle.remove();
        this.overflowToggle = null;
    }

    addOverflowButton() {
        if (this.overflowToggle) {
            return this.overflowToggle.querySelector(".dropdown-menu");
        }
        const item = document.createElement("li");
        item.className = "nav-item dropdown o_extra_menu_items";
        const toggle = document.createElement("a");
        toggle.className = "nav-link dropdown-toggle o-no-caret";
        toggle.href = "#";
        toggle.dataset.bsToggle = "dropdown";
        toggle.innerHTML = '<i class="fa fa-plus"></i>';
        const menu = document.createElement("ul");
        menu.className = "dropdown-menu dropdown-menu-end";
        item.append(toggle, menu);
        this.el.append(item);
        this.overflowToggle = item;
        return menu;
    }

    outerWidth(element) {
        const style = window.getComputedStyle(element);
        return element.offsetWidth + parseFloat(style.marginLeft) + parseFloat(style.marginRight);
    }
}

registry.category("public.interactions").add("theme_voltro.menu_overflow", MenuOverflow);
