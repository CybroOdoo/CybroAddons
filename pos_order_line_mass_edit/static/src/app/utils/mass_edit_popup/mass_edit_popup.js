/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class MassEditPopup extends Component {
    static template = "pos_order_line_mass_edit.MassEditPopup";
    static components = { Dialog };
    static defaultProps = {
        title: _t("Edit order lines"),
        confirmLabel: _t("Confirm"),
        cancelLabel: _t("Cancel"),
        closeLabel: _t("Close"),
        confirmClass: "btn-primary",
    };
    static props = {
        close: { type: Function },
        body: { type: Object, optional: true },
        confirm: { type: Function, optional: true },
        confirmLabel: { type: String, optional: true },
        confirmClass: { type: String, optional: true },
        cancel: { type: Function, optional: true },
        cancelLabel: { type: String, optional: true },
        closeLabel: { type: String, optional: true },
    };

    setup(){
        this.pos = usePos();
        this.state = useState({
            lines: this.props.body || [],
            lastDeleted: null
        });
    }

    updateQty(line, value) {
        const qty = parseFloat(value);
        if (!isNaN(qty)) {
            line.qty = qty;
        }
    }

    _confirm() {
        this.props.close();
    }

    sendInput(key) {
        const deletedLine = this.state.lines.find(order => order.id == key);
        if (deletedLine) {
            this.state.lastDeleted = {
                product: deletedLine.product_id,
                qty: deletedLine.qty,
                price: deletedLine.price_unit,
                discount: deletedLine.discount
            };
            const current_order = this.pos.getOrder();
            current_order.removeOrderline(deletedLine);
            this.state.lines = this.state.lines.filter(line => line.id !== key);
        }
    }

    async undoDelete() {
        if (this.state.lastDeleted) {
            const data = this.state.lastDeleted;
            await this.pos.addLineToCurrentOrder(
                {
                    product_id: data.product,
                    product_tmpl_id: data.product.product_tmpl_id,
                    qty: data.qty,
                    price_unit: data.price,
                    discount: data.discount
                }
            );

            const current_order = this.pos.getOrder();
            const newLine = current_order.getLastOrderline();
            this.state.lines.push(newLine);
            this.state.lastDeleted = null;
        }
    }
}
