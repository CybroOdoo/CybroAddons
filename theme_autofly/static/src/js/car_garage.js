/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.car_garage = publicWidget.Widget.extend({
    selector : '.car_garage_main_section',

    willStart: async function () {
        const data = await rpc('/get_garage_car',{})
        if(data){
            this.el.querySelector('.dynamic_snippet_garage_section').append(renderToElement('theme_autofly.portfolio_garage_page',
                {'car_garages': data.car_garages, 'car_types': data.car_types}
            ))
        }
    },

    start: function(){
        this.el.querySelector('.alert-info').style.display = 'none'
    },

});
