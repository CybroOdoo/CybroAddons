import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component, useProps, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class TransferRefPopup extends Component {
    static template = "stock_transfer_in_pos.TransferRefPopup";
    static components = { Dialog };
    props = useProps({
        title: t.string().optional(_t("Confirm?")),
        data: t.object().optional({}),
        confirmButtonLabel: t.string().optional("OK"),
        close: t.function(),
    });

    setup() {
        this.dialog = useService("dialog");
    }

    // Function to open the backend transfer view in a new tab without disrupting POS
    openStockTransfer() {
        const refId = this.props.data?.id;
        if (refId) {
            window.open(`/odoo/action-stock.action_picking_tree_all/${refId}`, "_blank");
        }
    }

    confirm() {
        this.props.close();
    }
}