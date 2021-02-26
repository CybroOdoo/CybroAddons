odoo.define('product_multi_uom_pos.uom_button',function(require) {
    "use strict";

var core = require('web.core');
var QWeb = core.qweb;

    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const { useState, useRef } = owl.hooks;
     const { Gui } = require('point_of_sale.Gui');



class UOMButton extends PosComponent {

        constructor() {
            super(...arguments);
            useListener('click', this.button_click);
        }

        button_click() {
            var orderline = this.env.pos.get_order().get_selected_orderline();
            var options = {
                'uom_list': orderline.product.uom_id
            };

             Gui.showPopup('MultiUomWidget',{options:options});
    }

}


UOMButton.template = 'UOMButton';
ProductScreen.addControlButton({

        component: UOMButton,
        condition: function () {
            return true;
        },
        position: ['before', 'SetFiscalPositionButton'],

    });

    Registries.Component.add(UOMButton);
    return UOMButton;



});