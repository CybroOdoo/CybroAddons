/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { PaymentForm } from "@payment/interactions/payment_form";

/**
 * Extend the PaymentForm interaction to save the customer note
 * before the payment flow is initiated and on input change.
 */
patch(PaymentForm.prototype, {

    setup() {
        super.setup();
        const customerNoteInput = document.getElementById("customer_note");
        if (customerNoteInput && !customerNoteInput.dataset.noteListenerAdded) {
            customerNoteInput.dataset.noteListenerAdded = "true";
            customerNoteInput.addEventListener("change", async () => {
                const saleOrderInput = document.querySelector("input[name='sale_order_id']");
                const orderId = saleOrderInput ? parseInt(saleOrderInput.value, 10) : null;
                const note = customerNoteInput.value.trim();
                try {
                    await rpc("/shop/save_customer_note", {
                        order_id: orderId,
                        customer_note: note,
                    });
                } catch (error) {
                    console.warn("Could not save customer note on change:", error);
                }
            });
        }
    },

    /**
     * Override submitForm to persist the customer note via RPC before
     * delegating to the original payment submission flow.
     *
     * @override
     */
    async submitForm(ev) {
        const customerNoteInput = document.getElementById("customer_note");
        const saleOrderInput = document.querySelector("input[name='sale_order_id']");

        if (customerNoteInput) {
            const note = customerNoteInput.value.trim();
            const orderId = saleOrderInput ? parseInt(saleOrderInput.value, 10) : null;
            try {
                await rpc("/shop/save_customer_note", {
                    order_id: orderId,
                    customer_note: note,
                });
            } catch (error) {
                console.warn("Could not save customer note on submit:", error);
            }
        }

        return super.submitForm(ev);
    },
});

