odoo.define('product_exchange_pos_sys.all_order_screen', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } =require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Qweb = core.qweb;
    const { onMounted, onWillUnmount, useState } = owl;

    class CustomOrdrScreen extends PosComponent {

        setup(){
            super.setup();
            useListener('click-order', this._onClickOrder);
            this.state = {
                order: this.props.orders,
                pos: this.env.pos
            };
        }

        back() {
            this.showScreen('ProductScreen');
        }
        _onClickOrder(order, pos){
            if (order.exchange == true){
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Exchange order'),
                    body: this.env._t('Already created the Exchange order')
                });
            }
            else{

                var lines = []
                for(var i = 0; i < order.lines.length; i++){
                        lines.push(order.lines[i])
                    }
                var self = this;
                this.rpc({
                       model: 'pos.order.line',
                        method: 'get_product_details',
                        args: [[], order.lines],
                }).then(function (value) {
                    self.showPopup('ExchangeOrder', {
                        'order_line' : value,
                        'pos': pos,
                        'order_id': order.id
                    });
                });
            }
        }
    };

  CustomOrdrScreen.template = 'CustomOrdrScreen';
  Registries.Component.add(CustomOrdrScreen);
  return CustomOrdrScreen;

});