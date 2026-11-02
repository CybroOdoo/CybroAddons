import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { getReportUrl } from "@web/webclient/actions/reports/utils";

/**
 * Open PDF reports in a new browser tab instead of downloading them.
 *
 * Only handles reports when the PDF engine is working and the tab could be
 * opened. Otherwise the handler returns false and the default report action
 * takes over: it shows the engine warning and falls back to the HTML report,
 * or downloads the PDF when the browser blocked the tab.
 */
async function pdfReportPreviewHandler(action) {
    if (!action.report_type.startsWith("qweb-pdf")) {
        return false;
    }
    const params = {};
    if (action.report_type.startsWith("qweb-pdf-")) {
        params.engine_name = action.report_type.slice("qweb-pdf-".length);
    }
    const state = await rpc("/report/get_pdf_engine_state", params);
    if (state !== "ok") {
        return false;
    }
    // Send the context like the default download does (active company,
    // language, report options). Only the "html" URL carries it for every
    // report, so build that one. It goes through the module route, which
    // redirects to a URL ending with the report file name so the browser tab
    // shows it instead of the record id.
    const context = { ...user.context, ...action.context };
    const url = getReportUrl({ ...action, context }, "html", context).replace(
        "/report/html/",
        "/report_attachment_preview/pdf/"
    );
    return Boolean(window.open(url));
}

registry
    .category("ir.actions.report handlers")
    .add("pdf_report_preview", pdfReportPreviewHandler);
