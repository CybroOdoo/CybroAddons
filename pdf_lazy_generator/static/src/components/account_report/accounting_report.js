/** @odoo-module **/

import { registry } from "@web/core/registry";
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


                        if (!options.report_id) {
                            console.error("[bg_pdf] options.report_id is missing! options keys:", Object.keys(options));
                            return super.buttonAction(ev, button);
                        }

                        try {
                            await this.env.services.rpc("/report/background_generate_accounting", {

                                options: options,
                                tab_id: UNIQUE_TAB_ID,
                            });
                            return;
                        } catch (e) {
                            console.error("[bg_pdf] RPC failed:", e);
                        }
                    }

                    return super.buttonAction(ev, button);
                },
            });
            AccountReportController.prototype._isBgPdfPatched = true;
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
