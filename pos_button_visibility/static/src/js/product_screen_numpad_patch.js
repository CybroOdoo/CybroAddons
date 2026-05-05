/** @odoo-module */
/**
 * Patch: ProductScreen (POS)
 *
 * This patch overrides the `getNumpadButtons` method to dynamically
 * control the availability of numpad actions (e.g., Discount, Price)
 * based on the logged-in cashier configuration.
 *
 * Behavior:
 * - Retrieves the current cashier and their allowed POS button settings.
 * - Extracts restricted button names from `pos_button_ids`.
 * - Stores them in `this.def` during component initialization.
 * - Overrides `getNumpadButtons()` to disable specific buttons
 *   depending on:
 *     - POS configuration (e.g., manual discount enabled)
 *     - Cashier permissions (e.g., price control rights)
 *     - Session-based restrictions (`pos_session_ids`)
 *
 * Notes:
 * - If no button configuration is defined, all numpad buttons behave normally.
 * - Button states are recalculated dynamically when rendering.
 */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

/** Patch ProductScreen for override the getNumpadButtons function  **/
patch(ProductScreen.prototype,{
    setup(){
        super.setup()
         // Get the POS cashier (logged-in user).
        const cashier = this.pos.cashier;
        // Session IDs selected on the user form (used to restrict buttons per session)
        this.pos_session_ids = cashier?.pos_session_ids.map(s => s.id);

        onWillStart(async () => {
            let buttons = [];
            const hideButtons = this.pos.cashier?.pos_button_ids;
            if (hideButtons) {
                buttons = hideButtons.map((button) => button.name);
            } else {
                buttons = false;
            }
            this.def = buttons;
        })
    },
    getNumpadButtons() {
        if (this.def){
            return [
                { value: "1" },
                { value: "2" },
                { value: "3" },
                { value: "quantity", text: "Qty" },
                { value: "4" },
                { value: "5" },
                { value: "6" },
                //here we are checking the condition
                { value: "discount", text: "% Disc", disabled: !this.pos.config.manual_discount || this.def.includes('Discount') && this.pos_session_ids.includes(this.pos.config.current_session_id.id) },
                { value: "7" },
                { value: "8" },
                { value: "9" },
                { value: "price", text: "Price", disabled: !this.pos.cashierHasPriceControlRights() ||this.def.includes('Price')&& this.pos_session_ids.includes(this.pos.config.current_session_id.id) },
                { value: "-", text: "+/-" },
                { value: "0" },
                { value: this.env.services.localization.decimalPoint },
                { value: "Backspace", text: "⌫" },
            ].map((button) => ({
                ...button,
                class: this.pos.numpadMode === button.value ? "active border-primary" : "",
            }));
        }
        else {
            return [
                { value: "1" },
                { value: "2" },
                { value: "3" },
                { value: "quantity", text: "Qty" },
                { value: "4" },
                { value: "5" },
                { value: "6" },
                { value: "discount", text: "% Disc"},
                { value: "7" },
                { value: "8" },
                { value: "9" },
                { value: "price", text: "Price"},
                { value: "-", text: "+/-" },
                { value: "0" },
                { value: this.env.services.localization.decimalPoint },
                { value: "Backspace", text: "⌫" },
            ].map((button) => ({
                ...button,
                class: this.pos.numpadMode === button.value ? "active border-primary" : "",
            }));
        }
    }
});
