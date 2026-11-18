/**
 * Propelle header.
 *
 * Adds the states of the floating bar to the standard header: light once the
 * page is scrolled (or from the top on the pages without a photo behind the
 * header), compact after 40px, and open while the mobile menu shows. Moves
 * the sliding indicator of the menu capsule, and makes the search button jump
 * to the property search of the page.
 */
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { prefersReducedMotion, scrollToElement } from "@theme_propelle/js/propelle_core";

export class PropelleHeader extends Interaction {
    static selector = "header.pp-header";
    dynamicContent = {
        _document: { "t-on-scroll": this.onScroll },
        _window: { "t-on-resize": this.moveIndicator },
        _root: {
            "t-att-class": () => ({
                "pp-is-scrolled": this.scrolled || this.light || this.menuOpen,
                "pp-is-compact": this.scrolled,
                "pp-menu-open": this.menuOpen,
            }),
        },
        ".offcanvas": {
            "t-on-show.bs.offcanvas": () => (this.menuOpen = true),
            "t-on-hide.bs.offcanvas": () => (this.menuOpen = false),
        },
        ".pp-nav__links": {
            "t-on-mouseleave": () => this.moveIndicator(),
            "t-att-class": () => ({ "pp-has-indicator": this.indicator }),
            "t-att-style": () => ({
                "--pp-ind-x": this.indicatorX,
                "--pp-ind-w": this.indicatorW,
            }),
        },
        ".pp-nav__link": {
            "t-on-mouseenter": (ev) => this.moveIndicator(ev.currentTarget),
        },
        ".pp-search-toggle": { "t-on-click": this.onSearchClick },
    };

    setup() {
        // Pages with a light hero keep the light bar from the top
        this.light = !this.el.closest(".o_header_overlay");
        this.scrolled = window.scrollY > 40;
        this.menuOpen = false;
        this.indicator = false;
        this.indicatorX = "0px";
        this.indicatorW = "0px";
        this.navEl = this.el.querySelector(".pp-nav__links");
    }

    start() {
        this.moveIndicator();
        if (document.fonts && document.fonts.ready) {
            this.waitFor(document.fonts.ready).then(() => {
                this.moveIndicator();
                this.updateContent();
            });
        }
    }

    onScroll() {
        this.scrolled = window.scrollY > 40;
    }

    /**
     * Place the indicator of the menu capsule under a link, or under the
     * active entry when no link is given.
     *
     * @param {HTMLElement} [target]
     */
    moveIndicator(target) {
        if (!this.navEl) {
            return;
        }
        if (!(target instanceof HTMLElement)) {
            target = this.navEl.querySelector(".pp-nav__link.active");
        }
        if (!target || !target.offsetWidth) {
            this.indicator = false;
            return;
        }
        this.indicatorX = target.offsetLeft + "px";
        this.indicatorW = target.offsetWidth + "px";
        this.indicator = true;
    }

    onSearchClick() {
        const wrap = this.el.closest("#wrapwrap");
        const menu = this.el.querySelector(".offcanvas.show");
        if (menu) {
            // global of Bootstrap
            window.Offcanvas.getInstance(menu)?.hide();
        }
        const target =
            wrap.querySelector(".pp-search-panel") ||
            wrap.querySelector("[data-listing-filters]");
        if (!target) {
            window.location.href = "/";
            return;
        }
        scrollToElement(target);
        this.waitForTimeout(
            () =>
                target
                    .querySelector(".pp-cselect__btn, select")
                    ?.focus({ preventScroll: true }),
            prefersReducedMotion() ? 0 : 500
        );
    }
}

registry.category("public.interactions").add("theme_propelle.header", PropelleHeader);
