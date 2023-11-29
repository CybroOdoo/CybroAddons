odoo.define('advanced_pos_reports.LocationSummaryButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");

    class LocationSummaryButton extends PosComponent {
         /**
            * @Override PosComponent
         */
        setup() {
            useListener('click', this._onClick);
        }
        async _onClick() {
            // Function to get all the location through rpc
            var locations = await this.rpc({
                   model: 'stock.location',
                    method: 'search_read',
                     args: [[['usage', '=', 'internal']]],
            });
            this.showPopup('LocationSummaryPopup', { title: 'Location Summary', locations: locations });
        }
    }
    LocationSummaryButton.template = 'LocationSummaryButton';
    ProductScreen.addControlButton({
      // Add button in product screen
        component: LocationSummaryButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(LocationSummaryButton);
    return LocationSummaryButton;
});
