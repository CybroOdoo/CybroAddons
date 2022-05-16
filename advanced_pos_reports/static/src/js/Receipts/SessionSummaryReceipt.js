odoo.define('advanced_pos_reports.SessionSummaryReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class SessionSummaryReceipt extends PosComponent {
        constructor() {
            super(...arguments);
            this._sessionSummaryEnv = this.props.session_summary
        }
        get session_summary() {
            return this._sessionSummaryEnv;
        }
        get company() {
            return this.env.pos.company;
        }
        get cashier() {
            return this.env.pos.get_cashier();
        }
    }
    SessionSummaryReceipt.template = 'SessionSummaryReceipt';

    Registries.Component.add(SessionSummaryReceipt);

    return SessionSummaryReceipt;
});
