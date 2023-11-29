odoo.define('advanced_pos_reports.LocationSummaryReceiptScreen', function (require) {
    'use strict';

    const { useRef } = owl;
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const LocationSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class LocationSummaryReceiptScreen extends AbstractReceiptScreen {
             /**
                * @Override AbstractReceiptScreen
             */
            setup() {
                super.setup();
                this.locationSummary = useRef('location-summary');
            }
            confirm() {
                //Returns to the product screen when we click confirm
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                //Method to print the receipt
                await this._printReceipt();
            }
        }
        LocationSummaryReceiptScreen.template = 'LocationSummaryReceiptScreen';
        return LocationSummaryReceiptScreen;
    };
    Registries.Component.addByExtending(LocationSummaryReceiptScreen, AbstractReceiptScreen);
    return LocationSummaryReceiptScreen;
});
