odoo.define('all_in_one_pos_kit.Orders', function (require) {
    'use strict';
   const PosComponent = require('point_of_sale.PosComponent');
   const { identifyError } = require('point_of_sale.utils');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');
    class OrderLineALL extends PosComponent {//Extension of the PosComponent class to add custom functionality to the order line component.
        setup() {// Perform setup tasks for the component.
           super.setup();
           // Attach a click listener to the component
           useListener('click', this.onClick);
        }
        /**
         * Handle the click event on the component.
         * Show the 'CustomOrdrScreen' with relevant data when clicked.
         */
        onClick() {
            this.showScreen('CustomOrdrScreen', {
                orders: this.env.pos.pos_orders,
                pos: this.env.pos
            });
        }
    }
   OrderLineALL.template = 'OrderLineALL';
   // Add the OrderLineALL component as a control button to the ProductScreen
       ProductScreen.addControlButton({
           component: OrderLineALL,
           condition: function() {
               return this.env.pos;
       },
   });
   // Register the OrderLineALL component with the Registries
   Registries.Component.add(OrderLineALL);
   return OrderLineALL;
});
