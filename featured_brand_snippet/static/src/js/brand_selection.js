/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";
import { uniqueId } from "@web/core/utils/functions";
import { _t } from "@web/core/l10n/translation";

// Split array into chunks for carousel slides
export function _chunk(array, size) {
    const result = [];

    if (!Array.isArray(array)) {
        return result;
    }

    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }

    return result;
}

const DEFAULT_PER_SLIDE = 4;
const DEFAULT_COL_CLASS = "col-12 col-sm-6 col-md-4 col-lg-3";

/**
 * Layout chosen in the demo: the number of demo cards left gives the number of
 * brands per slide, and the column classes of the first card give the card
 * width, offsets and auto margins, so the website looks like the demo. Slides
 * with fewer brands than demo cards keep the empty slots.
 */
export function _demoLayout(refEl) {
    const cardEls = refEl.querySelectorAll(".o_brand_demo_card");
    const colClasses = cardEls.length
        ? [...cardEls[0].parentElement.classList].filter((name) => /^(col(-|$)|offset-|mx-|ms-|me-)/.test(name))
        : [];
    return {
        perSlide: cardEls.length || DEFAULT_PER_SLIDE,
        colClass: colClasses.length ? colClasses.join(" ") : DEFAULT_COL_CLASS,
    };
}

/**
 * Replaces the static demo of the snippet with the real featured brands on the
 * website. The website editor does not start this interaction, so while
 * editing the static demo cards stay in place and can be edited or removed.
 * The demo cards left in the saved snippet set the layout on the website: how
 * many brands per slide (4 by default) and how wide each card is.
 */
export class ProductBrandDynamic extends Interaction {
    static selector = ".dynamic_snippet_brand";

    setup() {
        this.brands = [];
    }

    async willStart() {
        let response = [];
        try {
            response = await this.waitFor(rpc("/product_brand", {}));
        } catch {
            response = [];
        }
        // Handle both array and object responses
        this.brands = Array.isArray(response) ? response : response?.brands || [];
    }

    start() {
        const refEl = this.el.querySelector("#brands");
        if (!refEl) {
            return;
        }

        // Read the layout before the demo is removed.
        const { perSlide, colClass } = _demoLayout(refEl);

        // The demo children are restored when the interaction is destroyed.
        this.removeChildren(refEl);
        refEl.classList.remove("o_brand_demo");
        this.registerCleanup(() => refEl.classList.add("o_brand_demo"));

        const wrapperEl = document.createElement("div");
        if (this.brands.length) {
            // Pad every slide up to perSlide so empty slots keep their space.
            const chunks = _chunk(this.brands, perSlide).map((chunk) => [
                ...chunk,
                ...Array.from({ length: perSlide - chunk.length }, (_, i) => ({
                    id: `empty_${i}`,
                    empty: true,
                })),
            ]);
            wrapperEl.append(
                renderToFragment("featured_brand_snippet.brand_snippet_carousel", {
                    chunks: chunks,
                    colClass: colClass,
                    carouselId: `brand_carousel_${uniqueId()}`,
                })
            );
        } else {
            const messageEl = document.createElement("p");
            messageEl.className = "text-center";
            messageEl.textContent = _t("No brands found.");
            wrapperEl.append(messageEl);
        }
        // Removed again when the interaction is destroyed.
        this.insert(wrapperEl, refEl);
    }
}

registry
    .category("public.interactions")
    .add("featured_brand_snippet.product_brand", ProductBrandDynamic);
