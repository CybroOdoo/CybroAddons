odoo.define('advanced_pos_reports.OrderSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class OrderSummaryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        _onClick() {
            this.showPopup('OrderSummaryPopup', { title: 'Order Summary', });
//            const customer = this.env.pos.get_order().get_client();
//            const searchDetails = customer ? { fieldName: 'CUSTOMER', searchTerm: customer.name } : {};
//            this.trigger('close-popup');
//            this.showScreen('TicketScreen', {
//                ui: { filter: 'SYNCED', searchDetails },
//                destinationOrder: this.env.pos.get_order(),
//            });
        }
    }
    OrderSummaryButton.template = 'advanced_pos_reports.OrderSummaryButton';

    ProductScreen.addControlButton({
        component: OrderSummaryButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(OrderSummaryButton);

    return OrderSummaryButton;
});