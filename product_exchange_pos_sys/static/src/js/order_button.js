odoo.define('product_exchange_pos_sys.Orders', function (require) {
'use strict';
   const { Gui } = require('point_of_sale.Gui');
   const PosComponent = require('point_of_sale.PosComponent');
   const { identifyError } = require('point_of_sale.utils');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   class OrderLineALL extends PosComponent {
       setup() {
           super.setup();
           useListener('click', this.onClick);
       }
      onClick() {
        this.showScreen('CustomOrdrScreen', {
                orders: this.env.pos.pos_orders,
                pos: this.env.pos
            });

        }
   }

   OrderLineALL.template = 'OrderLineALL';
   ProductScreen.addControlButton({
       component: OrderLineALL,
       condition: function() {
           return this.env.pos;
       },
   });
   Registries.Component.add(OrderLineALL);
   return OrderLineALL;
});