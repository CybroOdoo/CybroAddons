/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
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

function getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
        if (type === "html") {
            const context = encodeURIComponent(JSON.stringify(env.services.user.context));
            url += `?context=${context}`;
        }
    }
    return url;
}
let wkhtmltopdfStateProm;

registry.category("ir.actions.report handlers").add("pdf_report_preview",
    async function (action, options, env) {
    let { report_type } = action;
    if (report_type !== "qweb-pdf")
        return false;
    if (!wkhtmltopdfStateProm) {
        wkhtmltopdfStateProm = await env.services.rpc("/report/check_wkhtmltopdf");
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
