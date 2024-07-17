/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { renderToElement } from "@web/core/utils/render";
export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
    var RatedProducts = PublicWidget.Widget.extend({
        selector: '.top_rated_product_snippet',
        willStart: async function() {
            var self = this;
            const data = await jsonrpc('/top_rated_products', {})
            const [products, categories, website_id, unique_id] = data
            Object.assign(this, {
                products, categories, website_id
            })
        },
        start: function () {
            const refEl = this.$el.find("#top_rated_carousel")
            const { products, categories, current_website_id, products_list} = this
            const chunkData = _chunk(products, 4)
            refEl.html(renderToElement('theme_eco_refine.top_rated_products', {
                products,
                categories,
                current_website_id,
                products_list,
                chunkData
            }))
            const element = document.body.querySelector("#topRatedCarousel")
            self.$('.owl-carousel').owlCarousel({
              loop: true,
              margin: 10,
              autoplay: true,
              nav: true,
              responsiveClass:true,
              responsive: {
                0: {
                  items: 1,
                   nav:true
                },
                600: {
                  items: 3,
                  nav:true
                },
                1000: {
                  items: 4,
                  nav:true
                }
              },
            });
        }
    });
    PublicWidget.registry.top_rated_product_snippet = RatedProducts;
    return RatedProducts;
