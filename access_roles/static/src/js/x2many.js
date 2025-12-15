/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { session } from "@web/session";

patch(Many2XAutocomplete.prototype, {
    setup() {
        super.setup();
        this.orm = this.env.services.orm;
        this._checkCreateAccess();
        // Ensure _checkCreateAccess runs whenever input changes
        const originalOnInput = this.onInput;
        this.onInput = async (...args) => {
            await this._checkCreateAccess();
            originalOnInput.apply(this, args);
        };
    },
    async _checkCreateAccess() {
        try {
            const targetModel = this.props.resModel;
            const userId = session.storeData.Store.settings.user_id.id;
            const result = await this.orm.call(
                "role.management",
                "check_model_access_restrictions",
                [userId, targetModel]
            );
                if (result) {
                if (result.is_hide_create) {
                    this.props.quickCreate = null;
                    if (this.props.activeActions) {
                        this.props.activeActions.createEdit = false;
                    }
                }
                if (result.is_model_readonly && this.props.activeActions) {
                    this.props.activeActions.createEdit = false;
                }
            }
        } catch (error) {
            console.error("Error checking model access restrictions:", error);
        }
    },
});
