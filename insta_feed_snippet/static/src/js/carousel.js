/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

/** Splits an array into smaller chunks of a given size. */
export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}

/** Interaction to fetch and display Instagram posts in a carousel. */
export class InstagramCarouselSnippet extends Interaction {
    static selector = ".s_carousel_template";

    setup() {
        this.uniqueId = Date.now();
        this.data = [];
    }

    async willStart() {
        this.data = await rpc("/get_dashboard_carousel", {});
    }

    start() {
        if (!this.data || !this.data.length) {
            return;
        }
        const chunks = _chunk(this.data, 3);
        if (chunks.length > 0 && chunks[0]) {
            chunks[0].is_active = true;
        }

        const container = this.el.querySelector("#instagram_carousel_container");
        if (container) {
            container.replaceChildren(
                renderToFragment("insta_feed_snippet.instagram_carousel_template", {
                    chunks: chunks,
                    unique_id: this.uniqueId,
                })
            );
        }
    }
}

registry
    .category("public.interactions")
    .add("insta_feed_snippet.carousel", InstagramCarouselSnippet);
