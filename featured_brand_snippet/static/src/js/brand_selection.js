/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToFragment } from "@web/core/utils/render";
//Creating a function for carousal slide data
export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
//Extending public widget to add dynamic product brand snippet
var ProductBrandDynamic = PublicWidget.Widget.extend({
        selector: '.dynamic_snippet_brand',
        willStart: async function () {
            const data = await rpc('/product_brand', {})
            this.data = data
        },

        start: function () {
            const refEl = this.$el.find("#brands")
            const chunks = _chunk(this.data, 4)
            refEl.html(renderToFragment('featured_brand_snippet.brand_snippet_carousel', {
                chunks
            }));
        return this._super.apply(this, arguments);
        },
    });
PublicWidget.registry.featured_brand_snippet = ProductBrandDynamic;
