/** @odoo-module **/
import { Component, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { LocationSummaryReceiptScreen } from "./LocationReceiptPopup";

export class LocationSummaryPopup extends Component {
    static components = { Dialog };
    static template = "advanced_pos_reports.LocationSummaryPopup";
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({
            selected_value: "",
        });
    }

    get locations() {
        return this.pos.models["stock.location"]?.getAll() || [];
    }

    async confirm() {
        const location = this.state.selected_value;
        if (!location) {
            return;
        }

        const locations = await this.orm.call("pos.config", "get_location_summary", [location]);
        if (locations && locations.length > 0) {
            await this.dialog.add(LocationSummaryReceiptScreen, {
                title: _t("Location Summary Receipt"),
                locations: locations,
                data: this.pos,
            });
        } else {
            await this.dialog.add(AlertDialog, {
                title: _t("No Data"),
                body: _t("No Data Available."),
            });
        }
    }
}
