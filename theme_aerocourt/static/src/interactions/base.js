/** Base interaction with a DOM rendering helper that restores the original markup on cleanup. */

import { Interaction } from "@web/public/interaction";

/**
 * Interaction base of the theme. Whatever an interaction renders into the page
 * is taken out again when it stops, so the website editor never saves it.
 */
export class AcInteraction extends Interaction {
    /**
     * Replaces the content of an element and restores the original markup when
     * the interaction is destroyed.
     *
     * @param {HTMLElement} el
     * @param {string} html
     */
    setHTML(el, html) {
        if (!el) {
            return;
        }
        this.originals ??= new Map();
        if (!this.originals.has(el)) {
            const original = el.innerHTML;
            this.originals.set(el, original);
            this.registerCleanup(() => {
                el.innerHTML = original;
            });
        }
        el.innerHTML = html;
    }
}
