/** @odoo-module **/
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { LocationSummaryReceiptScreen } from "./LocationReceiptPopup";

export class LocationSummaryPopup extends AbstractAwaitablePopup {
// Extending AbstractAwaitablePopup And Adding A Popup
    static template = 'LocationSummaryPopup';
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            selected_value: ''
        });
    }
    async confirm() {
// Get location summary
        var location = this.state.selected_value;
        if (location) {
            var locations = await this.orm.call('pos.config','get_location_summary', [this.config_id, location]);
            if (locations) {
                const { confirmed } = await this.pos.popup.add(LocationSummaryReceiptScreen,
                    {title: 'Location Receipt',locations: locations, data: this.pos}
                  );
            }
            else {
                await this.pos.popup.add(ErrorPopup, {
                    title: "No Data",
                    body: "No Data Available .",
                });
            }
        }
    }
}