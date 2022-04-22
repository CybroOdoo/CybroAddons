odoo.define('advanced_pos_reports.SessionSummaryPopup', function(require) {
    'use strict';

    const { useState } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useAutoFocusToLast } = require('point_of_sale.custom_hooks');
    const { _lt } = require('@web/core/l10n/translation');

    class SessionSummaryPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                selected_value: ''
            });
        }
        async confirm(event) {
            var session = this.state.selected_value;
            var session_summary = await this.rpc({
				model: 'pos.session',
				method: 'get_session_summary',
				args: [this.env.pos.pos_session.id, session],
				});
            this.showScreen('SessionSummaryReceiptScreen', { session_summary: session_summary});
            super.confirm();
        }
    }
    SessionSummaryPopup.template = 'SessionSummaryPopup';
    SessionSummaryPopup.defaultProps = {
        confirmText: _lt('Print'),
        cancelText: _lt('Cancel'),
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(SessionSummaryPopup);

    return SessionSummaryPopup;
});
