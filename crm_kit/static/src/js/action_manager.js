/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { _t } from "@web/core/l10n/translation";

/**
 * Handler responsible for generating XLSX reports.
 */
registry.category("ir.actions.report handlers").add("crm_kit.xlsx", async function (action, options, env) {
    if (action.report_type === 'xlsx') {
        if (env?.services?.ui) {
            env.services.ui.block();
        }
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } catch (error) {
            if (env?.services?.notification) {
                env.services.notification.add(
                    error?.data?.message || _t("Could not download the XLSX report."),
                    { type: "danger", sticky: true }
                );
            }
        } finally {
            if (env?.services?.ui) {
                env.services.ui.unblock();
            }
        }
        return true;
    }
});
