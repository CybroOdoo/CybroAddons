import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

/**
 * Download the XLSX reports of the sale report wizards.
 *
 * @param {Object} action report action with the data of the report
 * @param {Object} options action options
 * @param {Object} env web client environment
 * @returns {Promise<boolean|undefined>} true when the action is handled here
 */
async function xlsxReportHandler(action, options, env) {
    if (action.report_type !== "xlsx") {
        return;
    }
    env.services.ui.block();
    try {
        await download({ url: "/xlsx_reports", data: action.data });
    } finally {
        env.services.ui.unblock();
    }
    return true;
}

registry
    .category("ir.actions.report handlers")
    .add("sale_report_advanced_xlsx", xlsxReportHandler);
