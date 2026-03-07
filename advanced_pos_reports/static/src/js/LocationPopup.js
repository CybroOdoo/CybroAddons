/** @odoo-module **/
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { LocationSummaryReceiptScreen } from "./LocationReceiptPopup";
export class LocationSummaryPopup extends Component {
// Extending AbstractAwaitablePopup And Adding A Popup
    static components = { Dialog };
    static template = 'LocationSummaryPopup';
    static props = {
            title: 'Location Summary',
            close: "Cancel",
        }
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = useState({
            selected_value: ''
        });
    }
    async confirm() {
    // Get location summary
        var loc =  this.pos.models['stock.location'].getAll()
        var location = this.state.selected_value;
        if (location) {
            var locations = await this.orm.call('pos.config','get_location_summary', [this.config_id, location]);
            if (locations) {
                const { confirmed } = await this.dialog.add(LocationSummaryReceiptScreen,
                    {title: 'Location Receipt',locations: locations, data: this.pos}
                  );
            }
            else {
                await this.dialog.add(AlertDialog, {
                    title: "No Data",
                    body: "No Data Available .",
                });
            }

        }
    }
}
