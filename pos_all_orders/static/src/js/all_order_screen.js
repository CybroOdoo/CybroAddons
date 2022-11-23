odoo.define('pos_all_orders.all_order_screen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } =require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Qweb = core.qweb;
    const { onMounted, onWillUnmount, useState } = owl;

    class CustomALLOrdrScreen extends PosComponent {
        setup(){
            super.setup();

            this.state = {
                order: this.props.orders
            };
        }

        back() {
            this.showScreen('ProductScreen');
        }
    };

  CustomALLOrdrScreen.template = 'CustomALLOrdrScreen';
  Registries.Component.add(CustomALLOrdrScreen);
  return CustomALLOrdrScreen;

});