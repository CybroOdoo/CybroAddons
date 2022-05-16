odoo.define('advanced_pos_reports.LocationSummaryPopup', function(require) {
    'use strict';

    const { useState } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');

    class LocationSummaryPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                selected_value: ''
            });
        }
        async confirm(event) {
            var location = this.state.selected_value;
            var locations = await this.rpc({
				model: 'pos.config',
				method: 'get_location_summary',
				args: [this.config_id, location],
				});
            this.showScreen('LocationSummaryReceiptScreen', { locations: locations});
            super.confirm();
        }
    }
    LocationSummaryPopup.template = 'LocationSummaryPopup';
    LocationSummaryPopup.defaultProps = {
        confirmText: _lt('Print'),
        cancelText: _lt('Cancel'),
        array: [],
        isSingleItem: false,
    };

    Registries.Component.add(LocationSummaryPopup);

    return LocationSummaryPopup;
});
