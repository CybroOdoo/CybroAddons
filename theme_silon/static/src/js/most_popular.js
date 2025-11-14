/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.Popular = publicWidget.Widget.extend({
    // To extend public widget
    selector: '.most-popular',
    start: async function () {
        // To get data from controller.
        var self = this;
        await rpc('/get_popular_product', {}).then(function(data) {
            if(data){
                self.$target.html(data)
            }
        })
    }
})
