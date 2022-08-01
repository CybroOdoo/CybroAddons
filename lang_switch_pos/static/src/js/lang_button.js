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


//Button click event listen and events

class LangButton extends PosComponent {

        constructor() {
            super(...arguments);
            useListener('click', this.button_click);
        }

        button_click() {
        
             Gui.showPopup('LangWidget');
    }

}


LangButton.template = 'LangButton';
ProductScreen.addControlButton({

        component: LangButton,
        condition: function () {
            return true;
        },
        position: ['before', 'SetFiscalPositionButton'],

    });

    Registries.Component.add(LangButton);
    return LangButton;



});