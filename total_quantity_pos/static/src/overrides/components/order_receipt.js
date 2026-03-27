console.log("PPPP");
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";

patch(OrderReceipt.prototype, {
    get ItemCount() {

        try {
            const order = this.props.order;


            if (order.lines && Array.isArray(order.lines)) {

                const totalQty = order.lines.reduce((total, line) => {
                    return total + parseFloat(line.qty || 0);
                }, 0);

                return totalQty;
            }


        } catch (error) {
            return 0;
        }
    }
});