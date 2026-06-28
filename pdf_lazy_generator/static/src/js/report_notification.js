/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { ViewButton } from "@web/views/view_button/view_button";

if (!window.customReportTabId) {
    window.customReportTabId = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}
const UNIQUE_TAB_ID = window.customReportTabId;

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


patch(ViewButton.prototype, {
    async onClick(ev) {
        const clickParams = this.props.clickParams;
        const resId = this.props.record?.resId || null;
        const resModel = this.props.record?.resModel || null;
        const actionId = clickParams?.name || null;

        if (clickParams?.type === "object" && resId && resModel && actionId) {
            try {
                const result = await rpc("/web/dataset/call_kw", {
                    model: resModel,
                    method: actionId,
                    args: [[resId]],
                    kwargs: {},
                });

                if (result?.type === "ir.actions.report" && result?.report_type === "qweb-pdf") {
                    ev.preventDefault();
                    ev.stopPropagation();

                    await rpc("/report/background_generate", {
                        report_name: result.report_name,
                        docids: [resId],
                        tab_id: UNIQUE_TAB_ID,
                    });

                    this.env.services.notification.add(
                        "PDF generating in background.",
                        { title: "Processing PDF.", type: "success" }
                    );
                    return;
                }

                if (result) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    await this.env.services.action.doAction(result);
                    return;
                }

                ev.preventDefault();
                ev.stopPropagation();
                return;

            } catch (e) {
                console.warn("ViewButton object patch error:", e);
            }
        }

        if (actionId && resId && clickParams?.type === "action") {
            try {
                const report = await getReportInfo(actionId);

                if (report?.report_type === "qweb-pdf") {
                    ev.preventDefault();
                    ev.stopPropagation();

                    await rpc("/report/background_generate", {
                        report_name: report.report_name,
                        docids: [resId],
                        tab_id: UNIQUE_TAB_ID,
                    });

                    this.env.services.notification.add(
                        "PDF generating in background...",
                        { title: "Processing PDF.", type: "success" }
                    );
                    return;
                }
            } catch (e) {
                console.warn("ViewButton action patch error:", e);
            }
        }

        return super.onClick(ev);
    }
});


registry.category("services").add("custom_report_patch", {
    dependencies: ["action", "notification", "bus_service", "mail.store"],
    async start(env, { action, notification, bus_service, "mail.store": mailStore }) {

        bus_service.subscribe("pdf_download", (payload) => {
            console.log("pdf_download received payload:", payload);
            console.log("Current UNIQUE_TAB_ID:", UNIQUE_TAB_ID);

            if (!payload?.url) return;
            if (payload.tab_id && payload.tab_id !== UNIQUE_TAB_ID) return;

            const orderRef = payload.order_ref || "Document";

            setTimeout(() => {
                const a = document.createElement("a");
                a.href = payload.url;
                a.setAttribute("download", payload.name || `${orderRef}.pdf`);
                a.setAttribute("target", "_self");
                document.body.appendChild(a);
                a.click();
                setTimeout(() => document.body.removeChild(a), 1000);
            }, 300);

            notification.add(`${orderRef} downloaded successfully.`, {
                title: "Download Completed",
                type: "success",
            });

            // TAB-LEVEL ATOMIC RELOAD v14 (Conditional)
            // If this is the tab that initiated the request AND chatter attachment is enabled, we reload.
            if (payload.tab_id && payload.tab_id === UNIQUE_TAB_ID && payload.is_attach_pdf_in_chatter) {
                console.log("pdf_download: Initiating conditional tab-level atomic reload");
                setTimeout(() => {
                    console.log("pdf_download: Hardware reload triggered (Condition Met)");
                    action.doAction({
                        type: 'ir.actions.client',
                        tag: 'soft_reload',
                    });
                }, 30);
            }
        });

        bus_service.subscribe("pdf_error", (payload) => {
            console.log("pdf_error received payload:", payload);
            console.log("Current UNIQUE_TAB_ID:", UNIQUE_TAB_ID);

            if (payload.tab_id && payload.tab_id !== UNIQUE_TAB_ID) return;


            notification.add(payload.message || "An error occurred during PDF generation.", {
                title: payload.title || "PDF Generation Failed",
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
                            (act.context?.active_id ? [act.context.active_id] : []);
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
                            activeIds = controller.model.root.selection.map(r => r.resId);
                        } else if (controller?.props?.resId) {
                            activeIds = [controller.props.resId];
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

                    notification.add("PDF generation started in background.", {
                        title: "Success",
                        type: "success",
                    });

                    return;
                }

            } catch (e) {
                console.warn("doAction patch error:", e);
            }

            return originalDoAction(act, options);
        };
    },
});