odoo.define('pos_delete_orderline.ItemsCount', function(require) {
    'use strict';
   const { Gui } = require('point_of_sale.Gui');
   const PosComponent = require('point_of_sale.PosComponent');
   const { identifyError } = require('point_of_sale.utils');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');

   class ItemsCount extends PosComponent {
        setup() {
           super.setup();
       }
       get_items_count() {
            /**
            * Get the count of order lines in the current order.
            *
            * @returns {number} The number of order lines in the current order.
            */
            var order    = this.env.pos.get_order();
            var count = order.orderlines.length;
            return count
       }
       get_items_qty() {
            /**
            * Get the total quantity of items in the current order.
            *
            * @returns {number} The total quantity of items in the current order.
            */
            var order    = this.env.pos.get_order();
            var sum = 0;
            order.orderlines.forEach(function(t) {
                sum += t.quantity;
            })
            return sum
       }

   }
   ItemsCount.template = 'ItemsCount';
   ProductScreen.addControlButton({
       component: ItemsCount,
       condition: function() {
           return this.env.pos;
       },
   });
   Registries.Component.add(ItemsCount);
   return ItemsCount;

});