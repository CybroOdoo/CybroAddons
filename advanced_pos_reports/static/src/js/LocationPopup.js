odoo.define('advanced_pos_reports.LocationSummaryPopup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');
    const { useState } = owl;

    class LocationSummaryPopup extends AbstractAwaitablePopup {
         /**
            * @Override AbstractAwaitablePopup
          */
         setup() {
            super.setup();
            this.state = useState({
                selected_value: ''
            });
        }
        async confirm(event) {
            // Get location summary
            var location = this.state.selected_value;
            if (location) {
                var locations = await this.rpc({
                    model: 'pos.config',
                    method: 'get_location_summary',
                    args: [this.config_id, location],
                    });
                if (locations) {
                    this.showScreen('LocationSummaryReceiptScreen', { locations: locations});
                    super.confirm();
                }
                else {
                     this.showPopup('ErrorPopup', {
                        title: this.env._t('No data'),
                        body: this.env._t('There is no data.'),
                });
                }
            }
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
