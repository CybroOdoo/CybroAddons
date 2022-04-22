odoo.define('advanced_pos_reports.LocationSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class LocationSummaryButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        async _onClick() {
            var locations = await this.rpc({
                   model: 'stock.location',
                    method: 'search_read',
                     args: [[['usage', '=', 'internal']]],
                });
            this.showPopup('LocationSummaryPopup', { title: 'Location Summary', locations: locations });
        }
    }
    LocationSummaryButton.template = 'advanced_pos_reports.LocationSummaryButton';

    ProductScreen.addControlButton({
        component: LocationSummaryButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(LocationSummaryButton);

    return LocationSummaryButton;
});