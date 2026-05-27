/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class TransferRefPopup extends Component {
    static template = "stock_transfer_in_pos.TransferRefPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        data: {  type: Object, optional: true },
        confirmButtonLabel: { type: String, optional: true },
        close: Function,
    };
    static defaultProps = {
        title: _t("Confirm?"),
        confirmButtonLabel: "OK",
    };

    setup() {
    this.dialog = useService("dialog");
    }

    // Function for redirect to the backend transfer  view
    stock_view() {
    var ref_id = this.props.data.id
     location.href = '/web#id='+ ref_id +'&&model=stock.picking&view_type=form'
    }
    confirm(){
    this.props.close();
    }
}