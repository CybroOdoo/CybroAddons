/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

function cybrosysSupportItem(env) {
    return {
        type: "item",
        id: "cybrosys_support",
        description: _t("Cybrosys Support"),
        callback: () => {
            env.services.action.doAction({
                name: _t("Cybrosys Support"),
                type: "ir.actions.act_window",
                res_model: "client.support",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
            });
        },
        sequence: 62,
    };
}

registry.category("user_menuitems").add("cybrosys_support", cybrosysSupportItem);
