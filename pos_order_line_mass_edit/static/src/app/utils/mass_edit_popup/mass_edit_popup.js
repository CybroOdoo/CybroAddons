import {_t} from "@web/core/l10n/translation";
import {Dialog} from "@web/core/dialog/dialog";
import {Component, useProps, proxy, t} from "@odoo/owl";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";

export class MassEditPopup extends Component {
    static template = "pos_order_line_mass_edit.MassEditPopup";
    static components = {Dialog};

    props = useProps({
        close: t.function(),
        body: t.array().optional([]),
        title: t.string().optional(_t("Edit order lines")),
        closeLabel: t.string().optional(_t("Close")),
    });

    setup() {
        this.pos = usePos();
        this.state = proxy({
            lines: [...this.props.body],
            lastDeleted: null,
        });
    }

    get lines() {
        return this.state.lines;
    }

    get lastDeleted() {
        return this.state.lastDeleted;
    }

    updateQty(line, value) {
        const qty = parseFloat(value);
        if (!isNaN(qty)) {
            if (typeof line.setQuantity === "function") {
                line.setQuantity(qty);
            } else {
                line.qty = qty;
            }
        }
    }

    updatePrice(line, value) {
        const price = parseFloat(value);
        if (!isNaN(price)) {
            if (typeof line.setUnitPrice === "function") {
                line.setUnitPrice(price);
            } else {
                line.price_unit = price;
            }
        }
    }

    updateDiscount(line, value) {
        const discount = parseFloat(value);
        if (!isNaN(discount)) {
            if (typeof line.setDiscount === "function") {
                line.setDiscount(discount);
            } else {
                line.discount = discount;
            }
        }
    }

    deleteOrderLine(lineId) {
        const deletedLine = this.state.lines.find(
            (line) => line.id === lineId
        );

        if (!deletedLine) {
            return;
        }

        this.state.lastDeleted = {
            product: deletedLine.product_id,
            qty: deletedLine.qty,
            price: deletedLine.price_unit,
            discount: deletedLine.discount,
        };

        const currentOrder = this.pos.getOrder();
        if (currentOrder) {
            currentOrder.removeOrderline(deletedLine);
        }

        const index = this.state.lines.indexOf(deletedLine);
        if (index !== -1) {
            this.state.lines.splice(index, 1);
        }
    }

    async undoDelete() {
        if (!this.state.lastDeleted) {
            return;
        }

        const data = this.state.lastDeleted;

        const newLine = await this.pos.addLineToCurrentOrder({
            product_id: data.product,
            product_tmpl_id: data.product.product_tmpl_id,
            qty: data.qty,
            price_unit: data.price,
            discount: data.discount,
        });

        const line =
            newLine ||
            (this.pos.getOrder() && this.pos.getOrder().getLastOrderline());
        if (line) {
            this.state.lines.push(line);
        }
        this.state.lastDeleted = null;
    }
}
