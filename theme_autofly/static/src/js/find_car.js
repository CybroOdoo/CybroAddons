/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.findCar = animations.Animation.extend({
    selector : '.find_car_class',
    async start() {
        const data = await jsonrpc('/find_car')
        if(data){
            this.$target.empty().append(data);
        }
    }
});