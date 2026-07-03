/** @odoo-module **/

import paymentForm from "@payment/js/payment_form";

/**
 * Extend the existing PaymentForm legacy widget to save the customer note
 * before the payment flow is initiated.
 *
 * NOTE: In Odoo 17, PaymentForm is a legacy public Widget (not an OWL
 * component), so we must use .include() and this._super() — NOT patch() or
 * ES6 super().
 */
paymentForm.include({

    /**
     * Override _submitForm to persist the customer note via RPC before
     * delegating to the original payment submission flow.
     *
     * @override
     */
    async _submitForm(ev) {
        // In Odoo legacy classes, `this._super` is temporarily injected during
        // synchronous execution. Since this is an async function, we must stash
        // it before hitting any `await` so it's available after execution resumes.
        const superSubmit = this._super.bind(this);

        const customerNoteInput = document.getElementById("customer_note");
        const saleOrderInput = document.querySelector("input[name='sale_order_id']");

        if (customerNoteInput && saleOrderInput) {
            const note = customerNoteInput.value.trim();
            const orderId = parseInt(saleOrderInput.value, 10);
            if (orderId) {
                try {
                    await this.rpc("/shop/save_customer_note", {
                        order_id: orderId,
                        customer_note: note,
                    });
                } catch (error) {
                    console.warn("Could not save customer note:", error);
                }
            }
        }

        // Call the original _submitForm on the PaymentForm widget.
        return superSubmit(ev);
    },
});