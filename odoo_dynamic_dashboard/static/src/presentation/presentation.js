import { browser } from "@web/core/browser/browser";
import { formatDate } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, onWillUnmount, proxy, signal, t, useListener, useProps } from "@odoo/owl";
import { BLOCK_TYPES_BY_NAME } from "../block_catalog/block_catalog";
import { DashboardBlock } from "../dashboard_block/dashboard_block";

const KPIS_PER_SLIDE = 8;
export const AUTOPLAY_DELAY = 8000;

/**
 * Split the blocks of a dashboard into slides: a title slide, the key figures
 * gathered on a slide, each chart or table on its own slide, and text blocks as
 * section slides.
 *
 * @param {Object[]} blocks
 * @returns {{ type: "title"|"kpis"|"section"|"block", blocks?: Object[], block?: Object }[]}
 */
export function buildSlides(blocks) {
    const slides = [{ type: "title" }];
    let kpis = [];
    const flushKpis = () => {
        for (let index = 0; index < kpis.length; index += KPIS_PER_SLIDE) {
            slides.push({ type: "kpis", blocks: kpis.slice(index, index + KPIS_PER_SLIDE) });
        }
        kpis = [];
    };
    for (const block of blocks) {
        const { kind } = BLOCK_TYPES_BY_NAME[block.block_type];
        if (kind === "value") {
            kpis.push(block);
            continue;
        }
        flushKpis();
        slides.push({ type: kind === "static" ? "section" : "block", block });
    }
    flushKpis();
    return slides;
}

/**
 * Full screen slideshow of a dashboard.
 */
export class DashboardPresentation extends Component {
    static template = "odoo_dynamic_dashboard.DashboardPresentation";
    static components = { DashboardBlock };
    props = useProps({
        dashboard: t.object(),
        onClose: t.function(),
    });

    rootRef = signal.ref();

    setup() {
        this.slides = buildSlides(this.props.dashboard.blocks);
        this.today = formatDate(luxon.DateTime.local());
        this.state = proxy({ index: 0, autoplay: false });
        this.autoplayTimer = null;
        this.isFullscreen = false;

        useListener(window, "keydown", (ev) => this.onKeydown(ev));
        useListener(document, "fullscreenchange", () => this.onFullscreenChange());
        onMounted(() => {
            const root = this.rootRef();
            root?.focus();
            root?.requestFullscreen?.().then(
                () => (this.isFullscreen = true),
                () => {} // full screen refused (e.g. not from a click): present in the page
            );
        });
        onWillUnmount(() => {
            this.stopAutoplay();
            if (document.fullscreenElement) {
                document.exitFullscreen?.().catch(() => {});
            }
        });
    }

    getSlide() {
        return this.slides[this.state.index];
    }

    getKpiColumns(slide) {
        return Math.min(slide.blocks.length, 4);
    }

    getAutoplayTitle() {
        return this.state.autoplay ? _t("Pause") : _t("Play automatically");
    }

    getProgress() {
        return ((this.state.index + 1) / this.slides.length) * 100;
    }

    goTo(index) {
        this.state.index = Math.max(0, Math.min(index, this.slides.length - 1));
    }

    next() {
        if (this.state.index < this.slides.length - 1) {
            this.goTo(this.state.index + 1);
        } else if (this.state.autoplay) {
            this.goTo(0); // loop, e.g. on a wall screen
        }
    }

    previous() {
        this.goTo(this.state.index - 1);
    }

    toggleAutoplay() {
        if (this.state.autoplay) {
            this.stopAutoplay();
        } else {
            this.state.autoplay = true;
            this.autoplayTimer = browser.setInterval(() => this.next(), AUTOPLAY_DELAY);
        }
    }

    stopAutoplay() {
        this.state.autoplay = false;
        browser.clearInterval(this.autoplayTimer);
        this.autoplayTimer = null;
    }

    toggleFullscreen() {
        if (document.fullscreenElement) {
            this.isFullscreen = false;
            document.exitFullscreen?.();
        } else {
            this.rootRef()?.requestFullscreen?.().then(() => (this.isFullscreen = true), () => {});
        }
    }

    close() {
        this.props.onClose();
    }

    onFullscreenChange() {
        if (!document.fullscreenElement && this.isFullscreen) {
            // Escape leaves the browser full screen: end the presentation with it
            this.isFullscreen = false;
            this.close();
        }
    }

    onKeydown(ev) {
        switch (ev.key) {
            case "ArrowRight":
            case "ArrowDown":
            case "PageDown":
            case " ":
                ev.preventDefault();
                this.next();
                break;
            case "ArrowLeft":
            case "ArrowUp":
            case "PageUp":
                ev.preventDefault();
                this.previous();
                break;
            case "Home":
                this.goTo(0);
                break;
            case "End":
                this.goTo(this.slides.length - 1);
                break;
            case "Escape":
                this.close();
                break;
            case "f":
            case "F":
                this.toggleFullscreen();
                break;
        }
    }
}
