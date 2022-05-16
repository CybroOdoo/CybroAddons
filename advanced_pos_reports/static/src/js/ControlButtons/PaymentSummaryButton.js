odoo.define('advanced_pos_reports.PaymentSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class PaymentSummaryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        _onClick() {
            this.showPopup('PaymentSummaryPopup', { title: 'Payment Summary', });
        }
    }
    PaymentSummaryButton.template = 'advanced_pos_reports.PaymentSummaryButton';

    ProductScreen.addControlButton({
        component: PaymentSummaryButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(PaymentSummaryButton);

    return PaymentSummaryButton;
});