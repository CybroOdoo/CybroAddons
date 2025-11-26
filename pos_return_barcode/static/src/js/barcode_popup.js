/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";


export class BarcodePopup extends Component {
    static template = "BarcodePopup";
    static components = { Dialog };

    setup() {
        this.state = useState({ barcodeValue: "" });
        this.orm = useService("orm");
        this.dialog = useService("dialog")
        this.pos = usePos();
    }

    async confirm() {
         const barcode = this.state.barcodeValue.trim();
         const result = await this.orm.call("pos.order", "action_barcode_return", ["", barcode]);

        if (!result) {
            this.dialog.add(WarningDialog, {
                title: _t("Order not found"),
                message: _t("Invalid Entry, Order Not Found"),
            });
            return this.props.close();
        }

        const order = this.pos.get_order();
        const searchDetails = barcode ? { fieldName: "BARCODE", searchTerm: barcode } : {};
        this.pos.showScreen("TicketScreen", {
            stateOverride: {
                filter: "SYNCED",
                search: searchDetails,
                destinationOrder: order,
            },
        });
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
