import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    /**
     * Whether to show the delete button: only on the lines of the cart,
     * which OrderSummary marks with the o_pos_delete_orderline class.
     */
    get showDeleteButton() {
        return Boolean(this.props.class?.o_pos_delete_orderline);
    },

    /**
     * Remove the line from its order. A combo item removes its whole combo,
     * like removing it with the numpad does.
     */
    onClickDeleteLine() {
        const line = this.line.combo_parent_id || this.line;
        line.order_id.removeOrderline(line);
    },
});
