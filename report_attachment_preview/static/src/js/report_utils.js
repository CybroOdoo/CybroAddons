/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { getReportUrl } from "@web/webclient/actions/reports/utils";
import { rpc } from "@web/core/network/rpc";

/**
 * Retrieves messages related to the status of Wkhtmltopdf installation.
 *
 * @param {string} status - The status of Wkhtmltopdf installation.
 * @returns {string} The message related to the provided status.
 */
function getWKHTMLTOPDF_MESSAGES(status) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
    const _status = {
        broken: _t("Your installation of Wkhtmltopdf seems to be broken. The report will be shown in html.") + link,
        install: _t("Unable to find Wkhtmltopdf on this system. The report will be shown in html.") + link,
        upgrade: _t("You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to get a correct display of headers and footers as well as support for table-breaking between pages.") + link,
        workers: _t("You need to start Odoo with at least two workers to print a pdf version of the reports."),
    };
    return _status[status];
}
// Variable to store the state of Wkhtmltopdf installation
let wkhtmltopdfStateProm;
// Add PDF report preview handler to the report handlers registry
registry.category("ir.actions.report handlers").add("pdf_report_preview",
    async function (action, options, env) {
    // Check if the report type is 'qweb-pdf'
    let { report_type } = action;
    if (report_type !== "qweb-pdf")
        return false;
    if (!wkhtmltopdfStateProm) {
        wkhtmltopdfStateProm = await rpc("/report/check_wkhtmltopdf");
    }
    const state = wkhtmltopdfStateProm;
    const message = getWKHTMLTOPDF_MESSAGES(state);
    if (message) {
        env.services.notification.add(message, {
            sticky: true,
            title: _t("Report"),
        });
    }
    // If Wkhtmltopdf installation is successful, open the report in a new tab
    if (["upgrade", "ok"].includes(state)) {
        const url = getReportUrl(action, "pdf");
        window.open(url);
        return true;
    } else {
        return _executeReportClientAction(action, options);
    }
});
