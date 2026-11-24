/**
 * Nutivo motion layer.
 *
 * Smooth scrolling (Lenis), the hero intro and parallax, the scroll-reactive
 * ticker, word-by-word headings, fade-up reveals, card staggers, count-up
 * figures and image wipes of the Nutivo design, driven by GSAP and
 * ScrollTrigger. Without the libraries, or when the visitor prefers reduced
 * motion, blocks simply fade in when they enter the screen.
 *
 * Everything is reverted when the interaction stops (edit mode), so no
 * animation state is ever saved in the page.
 */
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const HEADING_SELECTOR = [
    ".nv-section-title",
    ".nv-goodness__title",
    ".nv-corporate__title",
    ".nv-newsletter__title",
    ".nv-about-cta__title",
].join(", ");
const WIPE_SELECTOR = ".nv-festive-card, .nv-goodness__img";
const COUNT_SELECTOR = ".nv-goodness__stats strong, .nv-stat__num";

export class NutivoMotion extends Interaction {
    static selector = ".nv-wrap";

    setup() {
        this.doc = this.el.ownerDocument;
        this.html = this.doc.documentElement;
        this.splitEls = new Map();
        this.counted = new Map();
        this.io = null;
    }

    start() {
        const { gsap, ScrollTrigger, Lenis } = window;
        const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        this.registerCleanup(() => this.revert());
        this.cloneTickers();
        if (reduce || !gsap || !ScrollTrigger) {
            this.observeReveals();
            return;
        }
        gsap.registerPlugin(ScrollTrigger);
        this.html.classList.add("nv-has-motion");
        if (Lenis) {
            this.setupLenis(gsap, ScrollTrigger, Lenis);
        }
        this.ctx = gsap.context(() => {
            this.setupHero(gsap);
            this.setupTicker(gsap, ScrollTrigger);
            this.setupHeadings(gsap);
            this.setupReveals(gsap, ScrollTrigger);
            this.setupCounts(gsap);
            this.setupWipes(gsap);
        }, this.el);
        // Lazy images change the layout height: recompute the trigger positions.
        this.addListener(window, "load", () => ScrollTrigger.refresh());
    }

    // ---------------------------------------------------------------------
    // Setup
    // ---------------------------------------------------------------------

    setupLenis(gsap, ScrollTrigger, Lenis) {
        const lenis = new Lenis({
            duration: 1.15,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        });
        this.lenis = lenis;
        lenis.on("scroll", ScrollTrigger.update);
        this.lenisRaf = (time) => lenis.raf(time * 1000);
        gsap.ticker.add(this.lenisRaf);
        gsap.ticker.lagSmoothing(0);
        // Pause while a drawer or a dialog locks the page.
        this.bodyObserver = new MutationObserver(() => {
            if (this.doc.body.classList.contains("nv-no-scroll") || this.doc.body.classList.contains("modal-open")) {
                lenis.stop();
            } else {
                lenis.start();
            }
        });
        this.bodyObserver.observe(this.doc.body, { attributes: true, attributeFilter: ["class"] });
        // Smooth in-page anchors with the header offset.
        this.addListener(this.el, "click", (ev) => {
            const link = ev.target.closest('a[href*="#"]');
            if (!link || ev.defaultPrevented) {
                return;
            }
            const [path, hash] = link.getAttribute("href").split("#");
            if (!hash || (path && path !== window.location.pathname)) {
                return;
            }
            const target = this.el.querySelector(`[id="${CSS.escape(hash)}"]`);
            if (!target) {
                return;
            }
            ev.preventDefault();
            lenis.scrollTo(target, { offset: -80, force: true });
            window.history.replaceState(null, "", `#${hash}`);
        });
    }

    setupHero(gsap) {
        const hero = this.el.querySelector(".nv-hero");
        const intro = gsap.timeline({ paused: true, defaults: { ease: "expo.out" } });
        const chrome = this.el.querySelectorAll(".nv-announce");
        if (chrome.length) {
            intro.from(chrome, { opacity: 0, duration: 1, clearProps: "opacity" }, 0);
        }
        if (hero) {
            for (const el of hero.querySelectorAll(".nv-reveal")) {
                el.classList.remove("nv-reveal");
                el.dataset.nvWasReveal = "1";
            }
            const frame = hero.querySelector(".nv-hero__frame");
            if (frame) {
                intro.from(frame, { opacity: 0, scale: 1.03, duration: 1.4 }, 0);
            }
            const words = this.splitWords(hero.querySelector(".nv-hero__title"));
            if (words.length) {
                intro.from(words, { yPercent: 115, duration: 1.3, stagger: 0.08, clearProps: "transform" }, 0.1);
            }
            const lines = [".nv-breadcrumb", ".nv-hero__est", ".nv-eyebrow", ".nv-hero__lede"]
                .map((sel) => hero.querySelector(sel))
                .filter(Boolean);
            if (lines.length) {
                intro.from(lines, { y: 26, opacity: 0, duration: 1.1, stagger: 0.1 }, 0.3);
            }
            const buttons = hero.querySelectorAll(".nv-hero__actions > *");
            if (buttons.length) {
                intro.from(buttons, { y: 26, opacity: 0, duration: 1.1, stagger: 0.1, clearProps: "transform" }, 0.5);
            }
            const heroST = () => ({ trigger: hero, start: "top top", end: "bottom top", scrub: true });
            const media = hero.querySelectorAll(".nv-hero__media img");
            if (media.length) {
                gsap.fromTo(media, { yPercent: -4, scale: 1.12 }, { yPercent: 4, scale: 1.12, ease: "none", scrollTrigger: heroST() });
            }
            const copy = hero.querySelector(".nv-hero__copy");
            if (copy) {
                gsap.to(copy, { y: -40, ease: "none", scrollTrigger: heroST() });
            }
            const feature = hero.querySelector(".nv-hero-feature");
            if (feature) {
                intro.from(feature, { x: 70, opacity: 0, duration: 1.3 }, 0.55);
                gsap.to(feature, { y: -40, ease: "none", scrollTrigger: heroST() });
                const ring = hero.querySelector(".nv-hero-feature__ring");
                if (ring) {
                    gsap.to(ring, { rotate: 90, transformOrigin: "50% 50%", ease: "none", scrollTrigger: heroST() });
                }
            }
        }
        intro.play();
    }

    /** Infinite ticker whose speed follows the scroll velocity. */
    setupTicker(gsap, ScrollTrigger) {
        for (const ticker of this.el.querySelectorAll(".nv-ticker")) {
            const track = ticker.querySelector(".nv-ticker__track");
            if (!track) {
                continue;
            }
            track.classList.add("nv-is-js");
            const loop = gsap.to(track, { xPercent: -50, duration: 42, ease: "none", repeat: -1 });
            ScrollTrigger.create({
                trigger: ticker,
                start: "top bottom",
                end: "bottom top",
                onUpdate: (self) => {
                    const boost = Math.min(6, Math.max(0, Math.abs(self.getVelocity()) / 220));
                    this.ctx.add(() => {
                        gsap.fromTo(
                            loop,
                            { timeScale: self.direction * (1 + boost) },
                            { timeScale: self.direction, duration: 1.2, ease: "power2.out", overwrite: true }
                        );
                    });
                },
            });
            const images = ticker.querySelectorAll(".nv-ticker__img");
            if (images.length) {
                gsap.from(images, {
                    scale: 0, rotate: -90, duration: 1.2, ease: "back.out(1.6)", stagger: 0.04,
                    scrollTrigger: { trigger: ticker, start: "top 90%", once: true },
                });
            }
        }
    }

    setupHeadings(gsap) {
        for (const title of this.el.querySelectorAll(HEADING_SELECTOR)) {
            const words = this.splitWords(title);
            if (!words.length) {
                continue;
            }
            gsap.from(words, {
                yPercent: 115, duration: 1.2, ease: "expo.out", stagger: 0.06,
                scrollTrigger: { trigger: title, start: "top 90%", once: true },
            });
        }
    }

    /** Batched fade-up reveals. */
    setupReveals(gsap, ScrollTrigger) {
        const reveals = [...this.el.querySelectorAll(".nv-reveal")];
        if (reveals.length) {
            gsap.set(reveals, { opacity: 0, y: 40 });
            ScrollTrigger.batch(reveals, {
                start: "top 92%",
                once: true,
                onEnter: (batch) => this.ctx.add(() => {
                    gsap.to(batch, {
                        opacity: 1, y: 0, duration: 1.2, ease: "expo.out", stagger: 0.09,
                        onComplete: () => {
                            for (const el of batch) {
                                el.classList.add("nv-is-visible");
                            }
                            gsap.set(batch, { clearProps: "transform,opacity" });
                        },
                    });
                }),
            });
        }
    }

    setupCounts(gsap) {
        for (const el of this.el.querySelectorAll(COUNT_SELECTOR)) {
            const match = /^([\d,]+)(.*)$/.exec(el.textContent.trim());
            if (!match) {
                continue;
            }
            this.counted.set(el, el.textContent);
            // Keep "12,400" grouping, but not for years like 2014.
            const grouped = match[1].includes(",");
            const end = Number(match[1].replace(/,/g, ""));
            const suffix = match[2];
            const show = (v) => `${grouped ? Math.round(v).toLocaleString("en-IN") : Math.round(v)}${suffix}`;
            // Years count up from a nearby year.
            const state = { v: end > 1900 && end < 2100 && !grouped ? end - 12 : 0 };
            el.textContent = show(state.v);
            gsap.to(state, {
                v: end, duration: 2, ease: "power2.out",
                scrollTrigger: { trigger: el, start: "top 92%", once: true },
                onUpdate: () => {
                    el.textContent = show(state.v);
                },
            });
        }
    }

    /** Image wipes with an inner parallax. */
    setupWipes(gsap) {
        for (const el of this.el.querySelectorAll(WIPE_SELECTOR)) {
            gsap.fromTo(el, { clipPath: "inset(22% 0% 0% 0%)" }, {
                clipPath: "inset(0% 0% 0% 0%)", duration: 1.6, ease: "expo.out",
                scrollTrigger: { trigger: el, start: "top 90%", once: true },
            });
            const img = el.tagName === "IMG" ? null : el.querySelector("img");
            if (img) {
                gsap.fromTo(img, { yPercent: -6, scale: 1.16 }, {
                    yPercent: 6, scale: 1.16, ease: "none",
                    scrollTrigger: { trigger: el, start: "top bottom", end: "bottom top", scrub: true },
                });
            }
        }
    }

    // ---------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------

    /**
     * Wrap every word of an element in a masked span.
     *
     * @param {HTMLElement} el
     * @returns {HTMLElement[]} the inner word spans
     */
    splitWords(el) {
        if (!el || this.splitEls.has(el)) {
            return [];
        }
        this.splitEls.set(el, [...el.childNodes].map((node) => node.cloneNode(true)));
        const words = [];
        const walk = (node) => {
            for (const child of [...node.childNodes]) {
                if (child.nodeType === Node.TEXT_NODE) {
                    const frag = this.doc.createDocumentFragment();
                    for (const part of child.textContent.split(/(\s+)/)) {
                        if (!part) {
                            continue;
                        }
                        if (/^\s+$/.test(part)) {
                            frag.append(this.doc.createTextNode(" "));
                            continue;
                        }
                        const word = this.doc.createElement("span");
                        word.className = "nv-sw";
                        const inner = this.doc.createElement("span");
                        inner.className = "nv-sw__in";
                        inner.textContent = part;
                        word.append(inner);
                        frag.append(word);
                        words.push(inner);
                    }
                    child.replaceWith(frag);
                } else if (child.nodeType === Node.ELEMENT_NODE && child.tagName !== "BR") {
                    walk(child);
                }
            }
        };
        walk(el);
        return words;
    }

    /** Double the ticker content so that the loop is seamless. */
    cloneTickers() {
        for (const track of this.el.querySelectorAll(".nv-ticker__track")) {
            const groups = track.querySelectorAll(".nv-ticker__group");
            if (groups.length !== 1) {
                continue;
            }
            const clone = groups[0].cloneNode(true);
            clone.setAttribute("aria-hidden", "true");
            clone.dataset.nvClone = "1";
            track.append(clone);
        }
    }

    /** Fallback: reveal blocks when they enter the screen. */
    observeReveals() {
        if (!("IntersectionObserver" in window)) {
            for (const el of this.el.querySelectorAll(".nv-reveal")) {
                el.classList.add("nv-is-visible");
            }
            return;
        }
        this.io = new IntersectionObserver((entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("nv-is-visible");
                    this.io.unobserve(entry.target);
                }
            }
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
        [...this.el.querySelectorAll(".nv-reveal:not(.nv-is-visible)")].forEach((el, i) => {
            el.style.transitionDelay = `${(i % 4) * 70}ms`;
            this.io.observe(el);
        });
    }

    /** Restore the page exactly as it was rendered. */
    revert() {
        this.io?.disconnect();
        this.ctx?.revert();
        if (this.lenis) {
            window.gsap.ticker.remove(this.lenisRaf);
            this.bodyObserver.disconnect();
            this.lenis.destroy();
        }
        for (const clone of this.el.querySelectorAll("[data-nv-clone]")) {
            clone.remove();
        }
        for (const [el, nodes] of this.splitEls) {
            el.replaceChildren(...nodes);
        }
        for (const [el, text] of this.counted) {
            el.textContent = text;
        }
        for (const el of this.el.querySelectorAll("[data-nv-was-reveal]")) {
            el.classList.add("nv-reveal");
            delete el.dataset.nvWasReveal;
        }
        for (const el of this.el.querySelectorAll(".nv-reveal")) {
            el.classList.remove("nv-is-visible");
            el.style.removeProperty("transition-delay");
        }
        for (const el of this.el.querySelectorAll(".nv-ticker__track.nv-is-js")) {
            el.classList.remove("nv-is-js");
        }
        this.html.classList.remove("nv-has-motion");
    }
}

registry.category("public.interactions").add("theme_nutivo.motion", NutivoMotion);
