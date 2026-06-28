/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";

if (!window.customReportTabId) {
    window.customReportTabId = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}
const UNIQUE_TAB_ID = window.customReportTabId;


function patchAccountReportController() {
    const modules = odoo.loader.modules;
    const moduleName = "@account_reports/components/account_report/controller";
    if (modules.has(moduleName)) {
        const { AccountReportController } = modules.get(moduleName);
        if (AccountReportController && !AccountReportController.prototype.hasOwnProperty("_isBgPdfPatched")) {
            patch(AccountReportController.prototype, {
                async buttonAction(ev, button) {
                    if (button.action === "export_file" && button.action_param === "export_to_pdf") {
                        const options =
                            this.model?.options ||
                            this.reportOptions ||
                            this.options ||
                            {};

                        console.log("[bg_pdf] Intercepted PDF export. options.report_id:", options.report_id);

                        if (!options.report_id) {
                            console.error("[bg_pdf] options.report_id is missing! options keys:", Object.keys(options));
                            return super.buttonAction(ev, button);
                        }

                        try {
                            await rpc("/report/background_generate_accounting", {
                                options: options,
                                tab_id: UNIQUE_TAB_ID,
                            });
                            this.env.services.notification.add(
                                "PDF is being generated in the background. It will download automatically when ready.",
                                { title: "Processing PDF.", type: "success" }
                            );
                            return;
                        } catch (e) {
                            console.error("[bg_pdf] RPC failed:", e);
                        }
                    }
                    return super.buttonAction(ev, button);
                },
            });
            AccountReportController.prototype._isBgPdfPatched = true;
            console.log("[bg_pdf] Successfully patched AccountReportController.");
        }
    }
}

patchAccountReportController();

if (odoo.loader && odoo.loader.bus) {
    odoo.loader.bus.addEventListener("module-started", (e) => {
        if (e.detail.moduleName === "@account_reports/components/account_report/controller") {
            patchAccountReportController();
        }
    });
}
