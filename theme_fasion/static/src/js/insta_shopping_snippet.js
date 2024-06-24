/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.insta_shopping = animations.Animation.extend({
    // To extend public widget
    selector: '._insta_shopping',
    start: async function () {
        // To get data from controller.
        var self = this;
        await jsonrpc('/get_insta_shopping', {}).then(function(data) {
            if(data){
                self.$target.html(data)
            }
        })
    }
})
