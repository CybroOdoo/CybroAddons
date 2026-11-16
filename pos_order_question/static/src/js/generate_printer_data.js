/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

/**
 * Patch GeneratePrinterData to inject question_list into each line data for ticket receipts.
 */
patch(GeneratePrinterData.prototype, {
    generateLineData() {
        const data = super.generateLineData(...arguments);
        for (const index in this.order.lines) {
            const line = this.order.lines[index];
            const lineData = data[index];
            if (lineData && line) {
                lineData.question_list = line.question_list || false;
            }
        }
        return data;
    },
});
