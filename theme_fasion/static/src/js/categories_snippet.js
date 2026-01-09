/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.Categories = publicWidget.Widget.extend({
    // To extend public widget
    selector: '._fasion_categories',
    start: async function () {
        // To get data from controller.
        var self = this;
        await rpc('/get_categories', {}).then(function(data) {
            if(data){
                  self.el.innerHTML = data;
            }
        })
    }
})
