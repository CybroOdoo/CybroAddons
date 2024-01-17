odoo.define('all_in_one_pos_kit.ItemsCount', function(require) {
    'use strict';
   const PosComponent = require('point_of_sale.PosComponent');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const Registries = require('point_of_sale.Registries');
   class ItemsCount extends PosComponent {
        setup() {
           super.setup();
       }
       get_items_count() {
            /**
            * Get the count of order lines in the current order.
            * @returns {number} The number of order lines in the current order.
            */
            return this.env.pos.get_order().orderlines.length
       }
       get_items_qty() {
            /**
            * Get the total quantity of items in the current order.
            * @returns {number} The total quantity of items in the current order.
            */
            var sum = 0;
            this.env.pos.get_order().orderlines.forEach(function(t) {
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
