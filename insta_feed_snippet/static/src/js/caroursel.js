/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";

/** Split an array into smaller chunks of a given size. */
export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}

/** Widget to fetch data and render an Instagram-style carousel snippet. */
var InstagramCarouselSnippet = publicWidget.Widget.extend({
    selector: '.s_carousel_template',

    init: function (parent) {
        this._super.apply(this, arguments);
        this.unique_id = Date.now();
    },

    willStart: async function () {
        const data = await rpc('/get_dashboard_carousel', {});
        this.data = data;
    },

    start: function () {
        const chunks = _chunk(this.data, 3);
        chunks[0].is_active = true;

        this.$el.find('#instagram_carousel_container').html(
            renderToFragment('insta_feed_snippet.instagram_carousel_template', {
                chunks: chunks,
                unique_id: this.unique_id
            })
        );
        return this._super.apply(this, arguments);
    },
});

publicWidget.registry.insta_feed_snippet = InstagramCarouselSnippet;