import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

/**
 * XLSX Report Handler
 * This handler is responsible for generating XLSX reports.
 * It sends a request to the server to generate the report in XLSX format
 * and downloads the generated file.
 * @param {Object} action - The action object containing the report details.
 * @param {Object} options - Additional action options.
 * @param {Object} env - The OWL environment containing services.
 * @returns {Promise<boolean>} - Resolves to true when the report generation is complete.
 */
registry.category("ir.actions.report handlers").add("xlsx", async (action, options, env) => {
    if (action.report_type === 'xlsx') {
        env?.services?.ui?.block();
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } finally {
            env?.services?.ui?.unblock();
        }
        return true;
    }
});
