/** @odoo-module **/
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class MassEditPopup extends Component {
    static template = "all_in_one_pos_kit.MassEditPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        body: { type: Array },
        confirm: { type: String, optional: true },
        cancel: { type: String, optional: true },
        close: { type: Function },
        getPayload: { type: Function, optional: true },
    };
    static defaultProps = {
        confirm: "Confirm",
        cancel: "Cancel",
    };
    confirm() {
        if (this.props.getPayload) {
            this.props.getPayload(true);
        }
        this.props.close();
    }
    cancel() {
        this.props.close();
    }
    sendInput(line) {
        line.order_id.removeOrderline(line);
    }
    onQtyChange(line, ev) {
        line.set_quantity(ev.target.value);
    }
    onPriceChange(line, ev) {
        line.set_unit_price(ev.target.value);
    }
    onDiscountChange(line, ev) {
        line.set_discount(ev.target.value);
    }
}
