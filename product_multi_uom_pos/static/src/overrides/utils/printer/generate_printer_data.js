import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

patch(GeneratePrinterData.prototype, {
    /**
     * Override generateLineData to substitute the custom UoM name on lines
     * where the cashier has selected a non-default UoM.
     */
    generateLineData() {
        const linesData = super.generateLineData(...arguments);
        const lines = this.order.lines;
        for (let i = 0; i < linesData.length; i++) {
            const line = lines[i];
            if (line && line.custom_uom_name) {
                linesData[i].product_uom_name = line.custom_uom_name;
            }
        }
        return linesData;
    },
});
