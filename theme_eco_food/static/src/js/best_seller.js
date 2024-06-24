/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.ecoFoodBestSeller = animations.Animation.extend({
    selector : '.best_seller_products',
    async start() {
        var data = await jsonrpc('/get_best_seller')
        if (data) {
            this.$target.empty().append(renderToElement('theme_eco_food.eco_food_best_seller_snippet', {
                best_seller: data
            }))
        }
     }
});