/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.insta_shopping = publicWidget.Widget.extend({
    // To extend public widget
    selector: '._insta_shopping',
    start: async function () {
        // To get data from controller.
        var self = this;
        await rpc('/get_insta_shopping', {}).then(function(data) {
            if(data){
                  self.el.innerHTML = data;
            }
        })
    }
})
