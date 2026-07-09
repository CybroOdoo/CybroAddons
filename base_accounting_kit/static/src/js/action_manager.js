/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { _t } from "@web/core/l10n/translation";

// Action handler for the custom xlsx report action type.
registry.category("ir.actions.report handlers").add("xlsx", async (action, options, env) => {
    if (action.report_type === "xlsx") {
        env.services.ui.block();
        try {
            await download({
                url: "/xlsx_report",
                data: action.data,
            });
        } catch (error) {
            env.services.notification.add(
                error?.data?.message || _t("Could not download the XLSX report."),
                { type: "danger", sticky: true }
            );
        } finally {
            env.services.ui.unblock();
        }
        return true;
    }
});
