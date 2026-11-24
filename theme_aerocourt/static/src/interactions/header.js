/** Interactions of the header and footer: scroll state, open status, theme switch, back to top and year. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { configValue, getConfig, pad, prefersReducedMotion } from "./utils";

/**
 * Behaviour of the standard header of the website: glass style once scrolled,
 * hidden while reading down and back on the way up.
 */
export class AcHeader extends Interaction {
    static selector = "header#top";
    dynamicContent = {
        _window: { "t-on-scroll.noUpdate": this.onScroll },
        _root: { "t-on-focusin.noUpdate": this.onFocusIn },
    };

    setup() {
        this.root = document.documentElement;
        this.lastY = window.scrollY;
        // SVG filter references live here: the asset pipeline would rebase them in a stylesheet
        this.root.style.setProperty("--ac-knock-dark", "url(#knockout-black)");
        this.root.style.setProperty("--ac-knock-light", "url(#knockout-light)");
        this.root.classList.toggle("has-dark-hero", Boolean(document.querySelector(".ac-hero, .ac-page-hero")));
        this.registerCleanup(() => {
            this.root.style.removeProperty("--ac-knock-dark");
            this.root.style.removeProperty("--ac-knock-light");
            this.root.classList.remove("has-dark-hero", "ac-menu-open");
            this.el.classList.remove("is-scrolled", "is-hidden");
        });
    }

    start() {
        // The mobile menu is the standard offcanvas, flagged on the page while open
        const offcanvas = this.el.querySelector("#top_menu_collapse_mobile");
        if (offcanvas) {
            this.addListener(offcanvas, "show.bs.offcanvas", () => this.root.classList.add("ac-menu-open"));
            this.addListener(offcanvas, "hidden.bs.offcanvas", () => this.root.classList.remove("ac-menu-open"));
        }
        this.onScroll();
    }

    onScroll() {
        const y = window.scrollY;
        const header = this.el;
        header.classList.toggle("is-scrolled", y > 40);
        const busy =
            this.root.classList.contains("ac-menu-open") ||
            header.contains(document.activeElement) ||
            Boolean(header.querySelector(".dropdown-menu.show"));
        if (y <= header.offsetHeight || busy) {
            header.classList.remove("is-hidden");
        } else if (y > this.lastY + 6) {
            header.classList.add("is-hidden");
        } else if (y < this.lastY - 6) {
            header.classList.remove("is-hidden");
        }
        if (Math.abs(y - this.lastY) > 6) {
            this.lastY = y;
        }
    }

    onFocusIn() {
        this.el.classList.remove("is-hidden");
    }
}

/** The "Open now / Closed" pill of the hero, from the opening hours in the settings. */
export class AcOpenStatus extends Interaction {
    static selector = "[data-open-status]";
    dynamicContent = {
        _root: { "t-att-class": () => ({ "is-closed": !this.isOpen() }) },
        ".ac-status-pill__text": { "t-out": () => this.text() },
    };

    start() {
        // The status changes with the clock, not with a user action
        this.setSafeInterval(() => this.updateContent(), 60_000);
    }

    isOpen() {
        const { openHour, closeHour } = getConfig();
        const hour = new Date().getHours();
        return hour >= openHour && hour < closeHour;
    }

    text() {
        const { openHour, closeHour } = getConfig();
        return this.isOpen()
            ? _t("Open now · until %s:00", pad(closeHour))
            : _t("Closed · opens %s:00", pad(openHour));
    }
}

/** Light / dark switch of the header, remembered in this browser. */
export class AcThemeToggle extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        ".ac-theme-toggle": {
            "t-on-click": this.onToggle,
            "t-att-aria-label": () => this.label(),
            "t-att-title": () => this.label(),
            "t-att-aria-pressed": () => String(this.isLight()),
        },
    };

    setup() {
        this.root = document.documentElement;
        this.meta = document.querySelector('meta[name="theme-color"]');
        try {
            if (localStorage.getItem("aerocourt.theme") === "light") {
                this.root.dataset.theme = "light";
            }
        } catch {
            // no saved theme
        }
        this.syncMeta();
    }

    isLight() {
        return this.root.dataset.theme === "light";
    }

    label() {
        return this.isLight() ? _t("Switch to dark theme") : _t("Switch to light theme");
    }

    syncMeta() {
        this.meta?.setAttribute("content", this.isLight() ? "#f4f5ef" : "#101110");
    }

    onToggle() {
        const light = !this.isLight();
        if (!prefersReducedMotion()) {
            this.root.classList.add("ac-theme-switching");
            this.waitForTimeout(() => this.root.classList.remove("ac-theme-switching"), 400);
        }
        if (light) {
            this.root.dataset.theme = "light";
        } else {
            delete this.root.dataset.theme;
        }
        try {
            localStorage.setItem("aerocourt.theme", light ? "light" : "dark");
        } catch {
            // not saved: the theme still applies for this page
        }
        this.syncMeta();
    }
}

/** Scrolls back to the top of the page from the footer button. */
export class AcBackToTop extends Interaction {
    static selector = "#backToTop";
    dynamicContent = {
        _root: { "t-on-click": this.onClick },
    };

    onClick() {
        window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
        const home = document.getElementById("home") || document.body;
        if (!home.hasAttribute("tabindex")) {
            home.setAttribute("tabindex", "-1");
        }
        home.focus({ preventScroll: true });
    }
}

/** Current year in the copyright line of the footer. */
export class AcYear extends Interaction {
    static selector = "#year";
    dynamicContent = {
        _root: { "t-out": () => new Date().getFullYear() },
    };
}

/**
 * Hours, prices and counts of the club settings shown in the page text. The
 * page keeps editable sample text, replaced here and restored in the editor.
 */
export class AcConfigValue extends Interaction {
    static selector = "[data-ac]:not([data-count])";
    dynamicContent = {
        _root: { "t-out": () => configValue(this.el.dataset.ac) ?? this.el.textContent },
    };
}

const registryCategory = registry.category("public.interactions");
registryCategory.add("theme_aerocourt.header", AcHeader);
registryCategory.add("theme_aerocourt.open_status", AcOpenStatus);
registryCategory.add("theme_aerocourt.theme_toggle", AcThemeToggle);
registryCategory.add("theme_aerocourt.back_to_top", AcBackToTop);
registryCategory.add("theme_aerocourt.year", AcYear);
registryCategory.add("theme_aerocourt.config_value", AcConfigValue);
