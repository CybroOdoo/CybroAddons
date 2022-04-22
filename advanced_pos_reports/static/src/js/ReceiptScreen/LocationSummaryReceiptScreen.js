odoo.define('advanced_pos_reports.LocationSummaryReceiptScreen', function (require) {
    'use strict';

    const { Printer } = require('point_of_sale.Printer');
    const { is_email } = require('web.utils');
    const { useRef, useContext } = owl.hooks;
    const { useErrorHandlers, onChangeOrder } = require('point_of_sale.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const AbstractReceiptScreen = require('point_of_sale.AbstractReceiptScreen');

    const LocationSummaryReceiptScreen = (AbstractReceiptScreen) => {
        class LocationSummaryReceiptScreen extends AbstractReceiptScreen {
            constructor() {
                super(...arguments);
                this.locationSummary = useRef('location-summary');
            }
            confirm() {
                this.showScreen('ProductScreen');
            }
            async printSummary() {
                await this._printReceipt();
            }

        }
        LocationSummaryReceiptScreen.template = 'LocationSummaryReceiptScreen';
        return LocationSummaryReceiptScreen;
    };

    Registries.Component.addByExtending(LocationSummaryReceiptScreen, AbstractReceiptScreen);

    return LocationSummaryReceiptScreen;
});
