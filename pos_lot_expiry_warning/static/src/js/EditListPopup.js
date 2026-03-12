/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";

export class LotListPopup extends Component {
    static components = { Dialog };
    static template = "pos_lot_expiry_warning.LotListPopup";
    static props = {
        title: String,
        name: String,
        lotStock: { type: Array, optional: true },
        getPayload: Function,
        close: { type: Function, optional: true },
        isSingleItem: { type: Boolean, optional: true },
    };
    static defaultProps = {
        lotStock: [],
        isSingleItem: false,
    };
    setup() {
        this.dialog = useService("dialog");
        this.state = useState({
            lot_id: "0",
        });
    }
    confirm() {
        if (this.state.lot_id === "0") {
            this.dialog.add(AlertDialog, {
                title: _t("Lot/Serial Number Required"),
                body: _t("Please select a Lot/Serial number"),
            });
            return;
        }
        this.props.getPayload({
            newArray: [{ text: this.state.lot_id, _id: 0 }],
        });
        this.props.close();
    }
    cancel() {
        this.props.close();
    }
}
