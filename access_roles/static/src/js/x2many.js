/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { user } from "@web/core/user";

const modelRestrictionsCache = new Map();

patch(Many2XAutocomplete.prototype, {
    setup() {
        super.setup();
        this.orm = this.env.services.orm;
        this._checkCreateAccess();
    },
    async _checkCreateAccess() {
        try {
            const targetModel = this.props.resModel;
            if (!targetModel) {
                return;
            }
            let result;
            if (modelRestrictionsCache.has(targetModel)) {
                result = modelRestrictionsCache.get(targetModel);
            } else {
                const userId = user.userId;
                result = await this.orm.call(
                    "role.management",
                    "check_model_access_restrictions",
                    [userId, targetModel]
                );
                modelRestrictionsCache.set(targetModel, result);
            }
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
        } catch {
            // Fail gracefully when checking model access restrictions
        }
    },
});
