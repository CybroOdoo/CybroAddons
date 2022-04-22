odoo.define('advanced_pos_reports.LocationSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class LocationSummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._locationSummaryEnv = this.props.locations
        }
        get locations() {
            return this._locationSummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
    }
    LocationSummaryReceipt.template = 'LocationSummaryReceipt';

    Registries.Component.add(LocationSummaryReceipt);

    return LocationSummaryReceipt;
});
