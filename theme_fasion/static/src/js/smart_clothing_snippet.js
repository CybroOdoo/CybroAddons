/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.SmartClothing = animations.Animation.extend({
    // To extend public widget
    selector: '._fasion_smart_clothing',
    events: {
        'click .smart_clothing_category': 'onClickCategory',
    },
    start: async function () {
        // To get data from controller.
        var self = this;
        await jsonrpc('/get_smart_clothing', {}).then(function(data) {
            if(data){
                self.$target.html(data)
            }
        })
    },
    onClickCategory: async function (ev) {
        // To change products according to clicked category.
        var self = this;
        await jsonrpc('/get_smart_clothing', {
            current_id: parseInt(ev.currentTarget.dataset.order),
        }).then(function(data) {
            if(data){
                self.$target.html(data)
            }
        })
    }
})
