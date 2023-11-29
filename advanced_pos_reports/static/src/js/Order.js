odoo.define('advanced_pos_reports.OrderSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class OrderSummaryButton extends PosComponent {
        /**
            * @Override PosComponent
        */
       setup() {
            useListener('click', this._onClick);
        }
        _onClick() {
            //Show order summary popup
            this.showPopup('OrderSummaryPopup', { title: 'Order Summary', });
        }
    }
    OrderSummaryButton.template = 'OrderSummaryButton';
    ProductScreen.addControlButton({
      // Add button in product screen
        component: OrderSummaryButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(OrderSummaryButton);
    return OrderSummaryButton;
});
