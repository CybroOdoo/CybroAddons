/**
 * Propelle shared interactions.
 *
 * The toast and the back to top button of the layout, the fade in of the
 * sections on scroll, the themed dropdowns that stand in for the native
 * selects, the selects and counters filled with the listing data, and the
 * city carousel. Every change made to the page is undone when the
 * interactions stop, so the edit mode only saves the snippet markup.
 */
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const TOAST_EVENT = "propelle:toast";

export const prefersReducedMotion = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Show a short message in the toast of the layout.
 *
 * @param {String} message
 */
export function showToast(message) {
    window.dispatchEvent(new CustomEvent(TOAST_EVENT, { detail: message }));
}

/**
 * Scroll an element to the top of the viewport, below the floating header.
 *
 * @param {HTMLElement} el
 */
export function scrollToElement(el) {
    el.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
}

/**
 * Read a JSON value of the local storage, or the fallback when the storage is
 * unavailable.
 */
export const store = {
    get(key, fallback) {
        try {
            return JSON.parse(window.localStorage.getItem(key)) ?? fallback;
        } catch {
            return fallback;
        }
    },
    set(key, value) {
        try {
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch {
            // storage unavailable
        }
    },
    remove(key) {
        try {
            window.localStorage.removeItem(key);
        } catch {
            // storage unavailable
        }
    },
};

let dataPromise;
/**
 * Cities, property types, budgets and counts of the listings, loaded once.
 *
 * @returns {Promise<Object>}
 */
export function loadPropelleData() {
    if (!dataPromise) {
        dataPromise = rpc("/propelle/data").catch(() => {
            dataPromise = undefined;
            return null;
        });
    }
    return dataPromise;
}

export class PropelleToast extends Interaction {
    static selector = ".pp-toast";

    start() {
        this.addListener(window, TOAST_EVENT, (ev) => this.show(ev.detail));
        this.registerCleanup(() => {
            this.el.classList.remove("pp-is-visible");
            this.el.textContent = "";
        });
    }

    show(message) {
        this.el.textContent = message;
        this.el.classList.add("pp-is-visible");
        clearTimeout(this.timer);
        this.timer = this.waitForTimeout(() => this.el.classList.remove("pp-is-visible"), 2400);
    }
}

export class PropelleBackToTop extends Interaction {
    static selector = ".pp-back-to-top";
    dynamicContent = {
        _document: { "t-on-scroll": this.onScroll },
        _root: {
            "t-on-click": this.onClick,
            "t-att-class": () => ({ "pp-is-visible": this.visible }),
        },
    };

    setup() {
        this.visible = window.scrollY > 700;
    }

    onScroll() {
        this.visible = window.scrollY > 700;
    }

    onClick() {
        window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    }
}

export class PropelleReveal extends Interaction {
    static selector = ".pp-reveal";

    start() {
        if (prefersReducedMotion() || !("IntersectionObserver" in window)) {
            return;
        }
        this.el.classList.add("pp-reveal--armed");
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries.some((entry) => entry.isIntersecting)) {
                    this.el.classList.add("pp-is-visible");
                    observer.disconnect();
                }
            },
            { threshold: 0.1 }
        );
        observer.observe(this.el);
        this.registerCleanup(() => {
            observer.disconnect();
            this.el.classList.remove("pp-reveal--armed", "pp-is-visible");
        });
    }
}

const openSelects = new Set();
let selectCount = 0;

/**
 * Themed dropdown: the native select stays in the page (forms, filters and
 * reset keep working) and is visually replaced by a button and a listbox.
 */
export class PropelleSelect extends Interaction {
    static selector = ".pp-s select";

    start() {
        const select = this.el;
        const uid = "ppcs" + ++selectCount;
        const wrap = document.createElement("div");
        wrap.className = "pp-cselect";
        select.parentNode.insertBefore(wrap, select);
        wrap.appendChild(select);
        select.classList.add("pp-cselect__native");
        const tabIndex = select.getAttribute("tabindex");
        select.tabIndex = -1;
        select.setAttribute("aria-hidden", "true");

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "pp-cselect__btn";
        btn.id = uid + "-btn";
        btn.setAttribute("aria-haspopup", "listbox");
        btn.setAttribute("aria-expanded", "false");
        const valueEl = document.createElement("span");
        valueEl.className = "pp-cselect__value";
        btn.appendChild(valueEl);

        const list = document.createElement("ul");
        list.className = "pp-cselect__list";
        list.id = uid + "-list";
        list.setAttribute("role", "listbox");
        list.tabIndex = -1;
        btn.setAttribute("aria-controls", list.id);
        wrap.append(btn, list);

        // Point the existing <label> at the new button
        const scope = select.closest("form, .pp-s") || wrap.parentNode;
        const label = select.id && scope.querySelector(`label[for="${select.id}"]`);
        const labelHadId = label && Boolean(label.id);
        if (label) {
            label.id = label.id || uid + "-label";
            label.htmlFor = btn.id;
            btn.setAttribute("aria-labelledby", `${label.id} ${btn.id}`);
            list.setAttribute("aria-labelledby", label.id);
        } else if (select.getAttribute("aria-label")) {
            btn.setAttribute("aria-label", select.getAttribute("aria-label"));
        }

        let items = [];
        let active = -1;

        const render = () => {
            const opt = select.options[select.selectedIndex];
            valueEl.textContent = opt ? opt.textContent : "";
            items.forEach((li, i) =>
                li.setAttribute("aria-selected", String(i === select.selectedIndex))
            );
        };
        const setActive = (i, scroll = true) => {
            if (!items.length) {
                return;
            }
            active = Math.max(0, Math.min(items.length - 1, i));
            items.forEach((li, n) => li.classList.toggle("pp-is-active", n === active));
            list.setAttribute("aria-activedescendant", items[active].id);
            if (scroll) {
                items[active].scrollIntoView({ block: "nearest" });
            }
        };
        const close = (refocus) => {
            wrap.classList.remove("pp-is-open");
            btn.setAttribute("aria-expanded", "false");
            openSelects.delete(close);
            if (refocus) {
                btn.focus({ preventScroll: true });
            }
        };
        const open = () => {
            openSelects.forEach((closeOther) => closeOther());
            wrap.classList.add("pp-is-open");
            btn.setAttribute("aria-expanded", "true");
            setActive(select.selectedIndex);
            list.focus({ preventScroll: true });
            openSelects.add(close);
        };
        const choose = (i) => {
            const changed = i !== select.selectedIndex;
            select.selectedIndex = i;
            close(true);
            if (changed) {
                select.dispatchEvent(new Event("input", { bubbles: true }));
                select.dispatchEvent(new Event("change", { bubbles: true }));
            }
        };
        const build = () => {
            list.replaceChildren();
            items = Array.from(select.options).map((opt, i) => {
                const li = document.createElement("li");
                li.id = `${uid}-opt${i}`;
                li.className = "pp-cselect__option";
                li.setAttribute("role", "option");
                li.textContent = opt.textContent;
                // keep focus in the list
                li.addEventListener("mousedown", (ev) => ev.preventDefault());
                li.addEventListener("click", () => choose(i));
                li.addEventListener("mousemove", () => setActive(i, false));
                list.appendChild(li);
                return li;
            });
            render();
        };

        this.addListener(btn, "click", () =>
            wrap.classList.contains("pp-is-open") ? close(true) : open()
        );
        this.addListener(btn, "keydown", (ev) => {
            if (["ArrowDown", "ArrowUp", "Enter", " "].includes(ev.key)) {
                ev.preventDefault();
                open();
            }
        });

        let typed = "";
        let typedTimer;
        this.addListener(list, "keydown", (ev) => {
            switch (ev.key) {
                case "ArrowDown":
                    ev.preventDefault();
                    setActive(active + 1);
                    break;
                case "ArrowUp":
                    ev.preventDefault();
                    setActive(active - 1);
                    break;
                case "Home":
                    ev.preventDefault();
                    setActive(0);
                    break;
                case "End":
                    ev.preventDefault();
                    setActive(items.length - 1);
                    break;
                case "Enter":
                case " ":
                    ev.preventDefault();
                    choose(active);
                    break;
                case "Escape":
                    ev.preventDefault();
                    close(true);
                    break;
                case "Tab":
                    close(false);
                    break;
                default:
                    if (ev.key.length === 1) {
                        // Type-ahead: jump to the first option starting with
                        // the typed letters
                        typed += ev.key.toLowerCase();
                        clearTimeout(typedTimer);
                        typedTimer = setTimeout(() => {
                            typed = "";
                        }, 600);
                        const hit = items.findIndex((li) =>
                            li.textContent.toLowerCase().startsWith(typed)
                        );
                        if (hit > -1) {
                            setActive(hit);
                        }
                    }
            }
        });
        this.addListener(list, "blur", () =>
            setTimeout(() => {
                if (!wrap.contains(wrap.ownerDocument.activeElement)) {
                    close(false);
                }
            }, 0)
        );
        this.addListener(wrap.ownerDocument, "click", (ev) => {
            if (!ev.target.closest(".pp-cselect")) {
                close(false);
            }
        });

        // Keep the button in sync when scripts change the select
        const proto = HTMLSelectElement.prototype;
        for (const prop of ["value", "selectedIndex"]) {
            const desc = Object.getOwnPropertyDescriptor(proto, prop);
            Object.defineProperty(select, prop, {
                configurable: true,
                get() {
                    return desc.get.call(this);
                },
                set(value) {
                    desc.set.call(this, value);
                    render();
                },
            });
        }
        this.addListener(select, "change", render);
        const observer = new MutationObserver(build);
        observer.observe(select, { childList: true, subtree: true });
        if (select.form) {
            this.addListener(select.form, "reset", () => setTimeout(render, 0));
        }
        build();

        this.registerCleanup(() => {
            observer.disconnect();
            openSelects.delete(close);
            delete select.value;
            delete select.selectedIndex;
            select.classList.remove("pp-cselect__native");
            select.removeAttribute("aria-hidden");
            if (tabIndex === null) {
                select.removeAttribute("tabindex");
            } else {
                select.setAttribute("tabindex", tabIndex);
            }
            if (label) {
                label.htmlFor = select.id;
                if (!labelHadId) {
                    label.removeAttribute("id");
                }
            }
            wrap.parentNode.insertBefore(select, wrap);
            wrap.remove();
        });
    }
}

/**
 * Select filled with the cities or the property types of the listings:
 * `<select data-pp-options="cities|types">`. The options written in the
 * snippet are the fallback, and come back when the interaction stops.
 */
export class PropelleOptions extends Interaction {
    static selector = "select[data-pp-options]";

    async willStart() {
        this.data = await this.waitFor(loadPropelleData());
    }

    start() {
        const rows = this.data && this.data[this.el.dataset.ppOptions];
        if (!rows || !rows.length) {
            return;
        }
        const original = Array.from(this.el.children);
        const selected = this.el.value;
        const options = original.filter((opt) => opt.value === "all");
        for (const row of rows) {
            const opt = document.createElement("option");
            opt.value = row.value;
            opt.textContent = row.label;
            options.push(opt);
        }
        this.el.replaceChildren(...options);
        if (options.some((opt) => opt.value === selected)) {
            this.el.value = selected;
        }
        this.registerCleanup(() => this.el.replaceChildren(...original));
    }
}

/**
 * Counter of the listings: `<span data-pp-count="sale|rent|projects"
 * data-one="home" data-many="homes">`.
 */
export class PropelleCount extends Interaction {
    static selector = "[data-pp-count]";

    async willStart() {
        this.data = await this.waitFor(loadPropelleData());
    }

    start() {
        const count = this.data && this.data.counts[this.el.dataset.ppCount];
        if (count === undefined) {
            return;
        }
        const original = this.el.textContent;
        const { one, many } = this.el.dataset;
        this.el.textContent = `${count} ${count === 1 ? one : many}`;
        this.registerCleanup(() => {
            this.el.textContent = original;
        });
    }
}

export class PropelleCarousel extends Interaction {
    static selector = "[data-carousel]";

    start() {
        const carousel = this.el;
        const area = carousel.closest("section") || carousel.parentNode;
        const step = () => (carousel.querySelector(".pp-place")?.offsetWidth || 300) + 16;
        const atEnd = () =>
            carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 8;
        const go = (dir) => {
            const behavior = prefersReducedMotion() ? "auto" : "smooth";
            if (dir > 0 && atEnd()) {
                // loop back to the start
                carousel.scrollTo({ left: 0, behavior });
            } else if (dir < 0 && carousel.scrollLeft <= 4) {
                carousel.scrollTo({ left: carousel.scrollWidth, behavior });
            } else {
                carousel.scrollBy({ left: dir * step(), behavior });
            }
        };
        const prev = area.querySelector("[data-carousel-prev]");
        const next = area.querySelector("[data-carousel-next]");
        if (prev) {
            this.addListener(prev, "click", () => go(-1));
        }
        if (next) {
            this.addListener(next, "click", () => go(1));
        }
        if (prefersReducedMotion()) {
            return;
        }
        // Auto-advance every 3.5s; pauses while hovered, focused, touched or
        // while the tab is hidden
        let paused = false;
        let resumeTimer;
        const pause = () => {
            paused = true;
            clearTimeout(resumeTimer);
        };
        const resume = (delay = 0) => {
            clearTimeout(resumeTimer);
            resumeTimer = setTimeout(() => {
                paused = false;
            }, delay);
        };
        this.addListener(area, "mouseenter", pause);
        this.addListener(area, "mouseleave", () => resume());
        this.addListener(area, "focusin", pause);
        this.addListener(area, "focusout", () => resume());
        this.addListener(carousel, "touchstart", pause, { passive: true });
        this.addListener(carousel, "touchend", () => resume(5000), { passive: true });
        const interval = setInterval(() => {
            if (!paused && !carousel.ownerDocument.hidden) {
                go(1);
            }
        }, 3500);
        this.registerCleanup(() => {
            clearInterval(interval);
            clearTimeout(resumeTimer);
            carousel.scrollLeft = 0;
        });
    }
}

registry
    .category("public.interactions")
    .add("theme_propelle.toast", PropelleToast)
    .add("theme_propelle.back_to_top", PropelleBackToTop)
    .add("theme_propelle.reveal", PropelleReveal)
    .add("theme_propelle.select", PropelleSelect)
    .add("theme_propelle.options", PropelleOptions)
    .add("theme_propelle.count", PropelleCount)
    .add("theme_propelle.carousel", PropelleCarousel);
