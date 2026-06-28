import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    /**
     * Returns an array of { payment_method_name, reference } objects
     * for every payment line that has a user_payment_reference set.
     * This survives the "selected line" being cleared after validation.
     */
    getPaymentReferences() {
        const order = this.pos.getOrder();
        if (!order) return [];

        return (order.payment_ids || [])
            .filter((line) => line.user_payment_reference)
            .map((line) => ({
                name: line.payment_method_id?.name || line.name || "",
                reference: line.user_payment_reference,
            }));
    },

    /**
     * Convenience helper — returns the first reference as a plain string
     * (useful for single-payment orders / simple XML binding).
     */
    getFirstPaymentReference() {
        const refs = this.getPaymentReferences();
        return refs.length ? refs[0].reference : "";
    },
});



