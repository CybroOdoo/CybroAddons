/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

if (!window.pdfLazyGeneratorTabId) {
    window.pdfLazyGeneratorTabId = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}
const UNIQUE_TAB_ID = window.pdfLazyGeneratorTabId;

async function getReportInfo(actionId) {
    if (!isNaN(parseInt(actionId))) {
        const data = await rpc("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "search_read",
            args: [[["id", "=", parseInt(actionId)]]],
            kwargs: { fields: ["report_name", "report_type"], limit: 1 },
        });
        return data.length ? data[0] : null;
    }

    if (typeof actionId === "string" && actionId.includes(".")) {
        const data = await rpc("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "search_read",
            args: [[["report_name", "like", actionId.split(".")[1]]]],
            kwargs: { fields: ["report_name", "report_type"], limit: 1 },
        });
        if (data.length) return data[0];

        const action = await rpc("/web/action/load", {
            action_id: actionId,
        });
        if (action?.report_type === "qweb-pdf") {
            return { report_name: action.report_name, report_type: action.report_type };
        }
    }

    return null;
}

registry.category("services").add("pdf_lazy_generator_service", {
    dependencies: ["action", "notification", "bus_service"],
    async start(env, { action, notification, bus_service }) {

        bus_service.subscribe("pdf_download", (payload) => {
            if (!payload?.url) return;
            if (payload.tab_id && payload.tab_id !== UNIQUE_TAB_ID) return;

            const orderRef = payload.order_ref || _t("Document");

            setTimeout(() => {
                const a = document.createElement("a");
                a.href = payload.url;
                a.setAttribute("download", payload.name || `${orderRef}.pdf`);
                a.setAttribute("target", "_self");
                document.body.appendChild(a);
                a.click();
                setTimeout(() => document.body.removeChild(a), 1000);
            }, 300);

            notification.add(
                _t("%(orderRef)s downloaded successfully.", { orderRef }),
                {
                    title: _t("Download Completed"),
                    type: "success",
                }
            );

            if (payload.tab_id && payload.tab_id === UNIQUE_TAB_ID && payload.is_attach_pdf_in_chatter) {
                setTimeout(() => {
                    action.doAction({
                        type: "ir.actions.client",
                        tag: "soft_reload",
                    });
                }, 30);
            }
        });

        bus_service.subscribe("pdf_error", (payload) => {
            if (payload.tab_id && payload.tab_id !== UNIQUE_TAB_ID) return;

            notification.add(payload.message || _t("An error occurred during PDF generation."), {
                title: payload.title || _t("PDF Generation Failed"),
                type: "warning",
            });
        });

        const originalDoAction = action.doAction.bind(action);

        action.doAction = async function (act, options = {}) {
            try {
                let reportName = null;
                let activeIds = [];

                if (typeof act === "object" && act.type === "ir.actions.report") {
                    if (act.report_type === "qweb-pdf") {
                        reportName = act.report_name;
                        activeIds = act.context?.active_ids ||
                            options?.additionalContext?.active_ids ||
                            (act.context?.active_id ? [act.context.active_id] : []) ||
                            (act.res_ids ? (Array.isArray(act.res_ids) ? act.res_ids : [act.res_ids]) : []);

                        if (!activeIds.length) {
                            const controller = env.services.action.currentController;
                            if (controller?.props?.resId) {
                                activeIds = [controller.props.resId];
                            } else if (controller?.model?.root?.resId) {
                                activeIds = [controller.model.root.resId];
                            } else if (controller?.model?.root?.selection?.length) {
                                activeIds = controller.model.root.selection.map((r) => r.resId);
                            }
                        }
                    }
                }

                if (!reportName) {
                    const isNumeric = typeof act === "number" ||
                        (typeof act === "string" && !isNaN(parseInt(act)) && !act.includes("."));
                    const isXmlId = typeof act === "string" && act.includes(".");

                    if (isNumeric || isXmlId) {
                        const controller = env.services.action.currentController;

                        if (options?.additionalContext?.active_ids?.length) {
                            activeIds = options.additionalContext.active_ids;
                        } else if (controller?.model?.root?.selection?.length) {
                            activeIds = controller.model.root.selection.map((r) => r.resId);
                        } else if (controller?.props?.resId) {
                            activeIds = [controller.props.resId];
                        } else if (controller?.model?.root?.resId) {
                            activeIds = [controller.model.root.resId];
                        }

                        if (activeIds.length) {
                            const report = await getReportInfo(act);
                            if (report?.report_type === "qweb-pdf") {
                                reportName = report.report_name;
                            }
                        }
                    }
                }

                if (reportName && activeIds.length) {
                    await rpc("/report/background_generate", {
                        report_name: reportName,
                        docids: activeIds,
                        tab_id: UNIQUE_TAB_ID,
                    });

                    notification.add(_t("PDF generation started in background."), {
                        title: _t("Success"),
                        type: "success",
                    });
                    return;
                }

            } catch (e) {
                // Fallback to standard doAction on error
            }

            return originalDoAction(act, options);
        };
    },
});