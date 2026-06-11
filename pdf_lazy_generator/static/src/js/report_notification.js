/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ViewButton } from "@web/views/view_button/view_button";
import { status } from "@odoo/owl";

if (!window.customReportTabId) {
    window.customReportTabId = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}
const UNIQUE_TAB_ID = window.customReportTabId;


async function getReportInfo(actionId, rpcService) {
    if (!isNaN(parseInt(actionId)) && String(actionId).indexOf('.') === -1) {
        const data = await rpcService("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "search_read",
            args: [[["id", "=", parseInt(actionId)]]],
            kwargs: { fields: ["report_name", "report_type"], limit: 1 },
        });
        return data.length ? data[0] : null;
    }

    if (typeof actionId === "string" && actionId.includes(".")) {
        const data = await rpcService("/web/dataset/call_kw", {
            model: "ir.actions.report",
            method: "search_read",
            args: [[["report_name", "like", actionId.split(".")[1]]]],
            kwargs: { fields: ["report_name", "report_type"], limit: 1 },
        });
        if (data.length) return data[0];

        const action = await rpcService("/web/action/load", { action_id: actionId });
        if (action?.type === "ir.actions.report" || action?.report_type === "qweb-pdf") {
            return { report_name: action.report_name, report_type: action.report_type || "qweb-pdf" };
        }
    }
    return null;
}

const MODULE_MGMT_METHODS = [
    "button_immediate_uninstall",
    "button_immediate_install",
    "button_immediate_upgrade",
    "button_uninstall_wizard",
    "button_install",
    "button_upgrade",
];

patch(ViewButton.prototype, {
    async onClick(ev) {
        if (status(this) === "destroyed") return;
        const clickParams = this.props.clickParams;
        const resId = this.props.record?.resId || null;
        const resModel = this.props.record?.resModel || null;
        const actionId = clickParams?.name || null;

        if (clickParams?.type === "object" && resModel === "ir.module.module" && MODULE_MGMT_METHODS.includes(actionId)) {
            return super.onClick(ev);
        }

        if (clickParams?.type === "object" && resId && resModel && actionId) {
            try {
                const result = await this.env.services.rpc("/web/dataset/call_kw", {
                    model: resModel,
                    method: actionId,
                    args: [[resId]],
                    kwargs: {
                        context: Object.assign({}, this.env.services.user.context, { tab_id: UNIQUE_TAB_ID })
                    },
                });

                if (result?.type === "ir.actions.report" && result?.report_type === "qweb-pdf") {
                    ev.preventDefault();
                    ev.stopPropagation();

                    await this.env.services.rpc("/report/background_generate", {
                        report_name: result.report_name,
                        docids: result.docids || result.res_ids || [resId],
                        tab_id: UNIQUE_TAB_ID,
                        data: result.data || {}, // PRESERVE WIZARD DATA
                    });
                    return;
                }

                if (result && typeof result === "object" && result.type) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    const actionService = this.env.services.action;
                    return actionService.doAction(result, {
                        additionalContext: { tab_id: UNIQUE_TAB_ID }
                    });
                }

                if (result !== undefined) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
                return;
            } catch (e) {
                console.warn("[bg_pdf] ViewButton object error:", e);
            }
        }

        // --- Handle type="action" ---
        if (actionId && resId && clickParams?.type === "action") {
            try {
                const report = await getReportInfo(actionId, this.env.services.rpc);
                if (report?.report_type === "qweb-pdf") {
                    ev.preventDefault();
                    ev.stopPropagation();

                    await this.env.services.rpc("/report/background_generate", {
                        report_name: report.report_name,
                        docids: [resId],
                        tab_id: UNIQUE_TAB_ID,
                        data: {},
                    });
                    return;
                }
            } catch (e) {
                console.warn("[bg_pdf] ViewButton action error:", e);
            }
        }

        return super.onClick(ev);
    }
});


registry.category("services").add("custom_report_patch", {
    dependencies: ["action", "notification", "bus_service", "user", "rpc"],
    async start(env, { action, notification, bus_service, user, rpc }) {

        // Inject tab_id into user context globally.
        Object.assign(user.context, { tab_id: UNIQUE_TAB_ID });

        bus_service.subscribe("pdf_started", (p) => {
            if (p.tab_id === UNIQUE_TAB_ID) {
                notification.add("PDF is being generated in the background. It will download automatically when ready.", {
                    title: "PDF Generation Started",
                    type: "success"
                });
            }
        });

        bus_service.subscribe("pdf_download", (payload) => {
            if (!payload?.url || payload.tab_id !== UNIQUE_TAB_ID) return;

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

            notification.add(`${orderRef} downloaded successfully.`, { title: "Done", type: "success" });

            // TAB-LEVEL ATOMIC RELOAD (Conditional)
            // If this is the tab that initiated the request AND chatter attachment is enabled, we reload.
            if (payload.tab_id && payload.tab_id === UNIQUE_TAB_ID && payload.is_attach_pdf_in_chatter) {
                setTimeout(() => {
                    action.doAction({
                        type: 'ir.actions.client',
                        tag: 'soft_reload',
                    });
                }, 30);
            }
        });

        bus_service.subscribe("pdf_error", (p) => {
            if (p.tab_id === UNIQUE_TAB_ID) notification.add(p.message || "Error generating PDF.", { title: "Failed", type: "danger", sticky: true });
        });

        const originalDoAction = action.doAction.bind(action);
        action._originalDoAction = originalDoAction;

        action.doAction = async function (act, options = {}) {
            if (!options.additionalContext) options.additionalContext = {};
            if (!options.additionalContext.tab_id) options.additionalContext.tab_id = UNIQUE_TAB_ID;

            try {
                let reportName = null;
                let activeIds = [];
                let reportData = {};

                if (typeof act === "object" && act !== null && act.type === "ir.actions.report" && act.report_type === "qweb-pdf") {
                    reportName = act.report_name;
                    reportData = act.data || {};
                    activeIds = act.docids || act.res_ids || [];
                    if (!Array.isArray(activeIds)) activeIds = activeIds ? [activeIds] : [];

                    if (!activeIds.length) {
                        activeIds = options.additionalContext?.active_ids || options.active_ids || (act.context?.active_ids) || (act.res_id ? [act.res_id] : []);
                    }
                }
                else if (typeof act === "number" || typeof act === "string") {
                    const resIds = options.additionalContext?.active_ids || options.active_ids || [];
                    if (resIds.length) {
                        const report = await getReportInfo(act, rpc);
                        if (report?.report_type === "qweb-pdf") {
                            reportName = report.report_name;
                            activeIds = resIds;
                        }
                    } else {
                        try {
                            const controller = action.currentController;
                            const root = controller?.model?.root;
                            const discoveryIds = root?.selection?.length ? root.selection.map(r => r.resId) : (root?.resId ? [root.resId] : []);
                            if (discoveryIds.length) {
                                const report = await getReportInfo(act, rpc);
                                if (report?.report_type === "qweb-pdf") {
                                    reportName = report.report_name;
                                    activeIds = discoveryIds;
                                }
                            }
                        } catch (e) { }
                    }
                }

                if (reportName && activeIds.length) {
                    rpc("/report/background_generate", {
                        report_name: reportName,
                        docids: Array.isArray(activeIds) ? activeIds : [activeIds],
                        tab_id: UNIQUE_TAB_ID,
                        data: reportData,
                    }).catch(e => console.warn("[bg_pdf] RPC error:", e));
                    return true;
                }
            } catch (e) {
                console.warn("[bg_pdf] doAction error:", e);
            }
            return originalDoAction(act, options);
        };
    },
});