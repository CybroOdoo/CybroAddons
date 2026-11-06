/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

if (!window.pdfLazyGeneratorTabId) {
    window.pdfLazyGeneratorTabId = Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}
const UNIQUE_TAB_ID = window.pdfLazyGeneratorTabId;

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
                            return super.buttonAction(ev, button);
                        }

                        try {
                            await rpc("/report/background_generate_accounting", {
                                options: options,
                                tab_id: UNIQUE_TAB_ID,
                            });
                            this.env.services.notification.add(
                                _t("PDF is being generated in the background. It will download automatically when ready."),
                                { title: _t("PDF Generation Started"), type: "success" }
                            );
                            return;
                        } catch (e) {
                            return super.buttonAction(ev, button);
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