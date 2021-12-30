odoo.define('pos_delete_orderline.DeleteOrderLinesAll', function(require) {
'use strict';
   const { Gui } = require('point_of_sale.Gui');
   const PosComponent = require('point_of_sale.PosComponent');
   const { posbus } = require('point_of_sale.utils');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require('web.custom_hooks');
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   class OrderLineClearALL extends PosComponent {
       constructor() {
           super(...arguments);
           useListener('click', this.onClick);
       }
      async onClick() {
                const { confirmed} = await this.showPopup("ConfirmPopup", {
                       title: this.env._t('Clear Orders?'),
                       body: this.env._t('Are you sure you want to delete all orders from the cart?'),
                   });
                if(confirmed){

                    const order = this.env.pos.get_order();
                    order.remove_orderline(order.get_orderlines());
                }
       }

   }

   OrderLineClearALL.template = 'OrderLineClearALL';
   ProductScreen.addControlButton({
       component: OrderLineClearALL,
       condition: function() {
           return this.env.pos;
       },
   });
   Registries.Component.add(OrderLineClearALL);
   return OrderLineClearALL;
});