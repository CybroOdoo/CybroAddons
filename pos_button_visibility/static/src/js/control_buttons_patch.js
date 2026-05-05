/** @odoo-module */
/**
 * Patch: ControlButtons (POS Product Screen)
 *
 * This patch customizes the visibility of control buttons in the POS
 * product screen based on the current cashier's configuration.
 *
 * Behavior:
 * - Retrieves the logged-in cashier from the POS session.
 * - Extracts allowed/hidden button configurations from `pos_button_ids`.
 * - Stores button names in a reactive Owl state (`state.buttons`).
 * - Makes the list available for conditional rendering in XML templates.
 *
 * Notes:
 * - `pos_session_ids` is derived from the cashier and may be used
 *   for session-based conditions in templates.
 * - If no button configuration is found, buttons default to an empty list.
 */
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

//Patching ControlButtons
patch(ControlButtons.prototype, {
    async setup(){
        super.setup(...arguments);
        // Get the POS cashier (logged-in user).
        // These values are used for condition checking in the XML templates.
        const cashier = this.pos.cashier;
        this.pos_session_ids = cashier?.pos_session_ids.map(s => s.id);
        this.state = useState({
            buttons: [],
        })
        let buttons = [];
        const hideButtons = this.pos.cashier?.pos_button_ids;
        if (hideButtons){
            buttons = hideButtons.map((button) => button.name);
        }
        this.state.buttons = buttons;
    }
})
