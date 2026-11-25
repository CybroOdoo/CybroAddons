/** @odoo-module **/

import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { QzTrayPrinter } from "../utils/printer/qz_tray_printer";

patch(PosTicketPrinterPlugin.prototype, {
    async printWithFallback(options = {}) {
        const {
            iframe,
            image,
            webFallback = true,
            download,
            printer = this.defaultPrinter,
            fallbacks = this.config.receipt_printer_ids,
        } = options;
        const printerName = this.config.system_printer_name;

        if (
            !printerName?.trim() ||
            printer ||
            fallbacks?.length ||
            (this.hasReceiptPrinters && this.config.other_devices) ||
            download
        ) {
            return super.printWithFallback(...arguments);
        }

        try {
            const receipt = image || (await this.generateImage(iframe));
            await new QzTrayPrinter(printerName).print(receipt);
            return { successful: true };
        } catch {
            this.notification.add(
                webFallback
                    ? _t("QZ Tray printing failed. Opening the browser print dialog.")
                    : _t("QZ Tray printing failed. Check that QZ Tray is running and the printer is available."),
                { type: "warning" }
            );
            return super.printWithFallback(...arguments);
        }
    },
});
