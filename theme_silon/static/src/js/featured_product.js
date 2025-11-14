/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.Featured = publicWidget.Widget.extend({
    // To extend public widget
    selector: '.featured',
    start: async function () {
        // To get data from controller.
        var self = this;
        await rpc('/get_featured_product', {}).then(function(data) {
            if(data){
                self.$target.html(data)
            }
        })
    }
})
