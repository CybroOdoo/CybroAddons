/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.DealWeek = animations.Animation.extend({
    selector: '.deal',
    async start() {
        var self = this;
        // Call backend JSON endpoint to fetch the products marked as 'Deal of the Week'
        var data = await jsonrpc('/get_deal_of_the_week', {})
        if (data) {
            // Render the fetched product information on the webpage
            self.$target.empty().append(data);
        }
    }
});
