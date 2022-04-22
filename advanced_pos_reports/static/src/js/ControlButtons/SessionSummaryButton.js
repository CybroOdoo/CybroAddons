odoo.define('advanced_pos_reports.SessionSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class SessionSummaryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        async _onClick() {
            var sessions = await this.rpc({
                   model: 'pos.session',
                    method: 'search_read',
                    args: [[]],
                });
            this.showPopup('SessionSummaryPopup', { title: 'Session Summary', sessions: sessions});
        }
    }
    SessionSummaryButton.template = 'advanced_pos_reports.SessionSummaryButton';

    ProductScreen.addControlButton({
        component: SessionSummaryButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(SessionSummaryButton);

    return SessionSummaryButton;
});