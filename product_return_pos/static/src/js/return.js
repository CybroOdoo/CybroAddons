odoo.define('product_return_pos.return',function(require) {
    "use strict";


var models = require('point_of_sale.models');
var gui = require('point_of_sale.Gui');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t  = require('web.core')._t;
var session = require('web.session');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const { useState, useRef } = owl.hooks;
    const OrderManagementScreen = require('point_of_sale.OrderManagementScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');



class ReturnButton extends PosComponent {

        constructor() {
            super(...arguments);
            useListener('click', this.button_click);
        }

        button_click() {
            var orders = this.env.pos.orders;

             this.showScreen('OrderListScreenWidget',{orders:orders});
    }

}


ReturnButton.template = 'ReturnButton';
ProductScreen.addControlButton({

        component: ReturnButton,
        condition: function () {
            return true;
        },
        position: ['before', 'SetPricelistButton'],
    });

    Registries.Component.add(ReturnButton);
    return ReturnButton;



});