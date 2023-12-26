/** @odoo-module */

import animations from "@website/js/content/snippets.animation";
import { jsonrpc } from "@web/core/network/rpc_service";

    animations.registry.get_product_tab = animations.Class.extend({
        selector : '.product_tab_class',
        start: function(){
            var self = this;
            jsonrpc('/get_product_tab')
            .then(function (data) {
                if(data){
                    self.$target.empty().append(data);
                }
            });
        }
    });
