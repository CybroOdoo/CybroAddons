odoo.define('pos_delete_orderline.DeleteOrderLines', function(require) {
'use strict';

    const { useState, useRef, onPatched } = owl.hooks;
    const { useListener } = require('web.custom_hooks');
    const { onChangeOrder } = require('point_of_sale.custom_hooks');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const Orderline = require('point_of_sale.Orderline');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const OrderWidget = require('point_of_sale.OrderWidget');

    const OrderLineDelete = (Orderline) =>
       class extends Orderline {
       async clear_button_fun() {
                   this.trigger('numpad-click-input', { key: 'Backspace' });
                   this.trigger('numpad-click-input', { key: 'Backspace' });

        }

        };
    Registries.Component.extend(Orderline, OrderLineDelete);
    return OrderWidget;

});

