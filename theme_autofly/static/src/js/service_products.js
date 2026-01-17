/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.service_product = publicWidget.Widget.extend({
    selector: '.theme_autofly-service-products',

    willStart: async function () {
        const data = await rpc('/get_service_product')
        if(data){
            this.el.querySelector('.theme_autofly_product_service').append(renderToElement('theme_autofly.service_products', {
                hot_deals: data
            }))
        }
    },

    start: function(){
        this.el.querySelector('.alert-info').style.display = 'none'
    },
});
