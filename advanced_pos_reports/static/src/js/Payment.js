odoo.define('advanced_pos_reports.PaymentSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class PaymentSummaryButton extends PosComponent {
         /**
            * @Override PosComponent
         */
        setup() {
            useListener('click', this._onClick);
        }
        _onClick() {
            //Show payment summary popup
            this.showPopup('PaymentSummaryPopup', { title: 'Payment Summary', });
        }
    }
    PaymentSummaryButton.template = 'PaymentSummaryButton';
    ProductScreen.addControlButton({
      // Add button in product screen
        component: PaymentSummaryButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(PaymentSummaryButton);
    return PaymentSummaryButton;
});
