/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}
import { renderToElement } from "@web/core/utils/render";
    var NewArrivalProducts = PublicWidget.Widget.extend({
        selector: '.product_new_arrival_snippet',
        willStart: async function() {
            const data = await jsonrpc('/new_arrival_products', {})
            const [products, categories, website_id, unique_id] = data
            Object.assign(this, {
                products, categories, website_id, unique_id
            })
        },
        /**
         * Render the widget with the fetched data.
         */
         start: function () {
            const refEl = this.$el.find("#new_arrival_carousel")
            const { products, categories, current_website_id, products_list} = this
            const chunkData = _chunk(products, 4)
            refEl.html(renderToElement('theme_eco_refine.new_product_arrival', {
                products,
                categories,
                current_website_id,
                products_list,
                chunkData
            }))
            const element = document.body.querySelector("#myCarousel")
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
    PublicWidget.registry.product_new_arrival_snippet = NewArrivalProducts;
    return NewArrivalProducts;
