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
//  Function for best seller snippet
var TopSellingProducts = PublicWidget.Widget.extend({
        selector: '.best_seller_product_snippet',
        willStart: async function () {
            const data = await jsonrpc('/top_selling_products', {})
            const [products, categories, website_id, unique_id] = data
            Object.assign(this, {
                products, categories, website_id, unique_id
            })
        },
        start: function () {
            const refEl = this.$el.find("#top_products_carousel")
            const { products, categories, current_website_id, products_list} = this
            const chunkData = _chunk(products, 4)
            refEl.html(renderToElement('theme_eco_refine.products_category_wise', {
                products,
                categories,
                current_website_id,
                products_list,
                chunkData
            }))
        const element = document.body.querySelector("#bestSellCarousel")
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
        self.$(".owl-prev").click(function () {
      $(".owl-carousel").trigger("prev.owl.carousel");
    });
    self.$("owl-next").click(function () {
      $(".owl-carousel").trigger("next.owl.carousel");
    });
        }
    });
PublicWidget.registry.products_category_wise_snippet = TopSellingProducts;
return TopSellingProducts;
