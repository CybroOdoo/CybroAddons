odoo.define('advanced_pos_reports.LocationSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class LocationSummaryReceipt extends PosComponent {
         /**
            * @Override PosComponent
         */
        setup() {
            super.setup();
            this._locationSummaryEnv = this.props.locations
        }
        get locations() {
            //Get location details
            return this._locationSummaryEnv;
        }
        get company() {
            //Get company details
            return this.env.pos.company;
        }
        get cashier() {
            //Get cashier details
            return this.env.pos.get_cashier();
        }
    }
    LocationSummaryReceipt.template = 'LocationSummaryReceipt';
    Registries.Component.add(LocationSummaryReceipt);
    return LocationSummaryReceipt;
});
