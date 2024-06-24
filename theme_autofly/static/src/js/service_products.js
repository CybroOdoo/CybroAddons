/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.service_product = publicWidget.Widget.extend({
    selector: '.product_service',
    async start(){
        const data = await jsonrpc('/get_service_product')
        if(data){
            this.$target.empty().append(data);
        }
    }
});