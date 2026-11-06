import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

patch(GeneratePrinterData.prototype, {
    generateLineData() {
        const data = super.generateLineData(...arguments);
        for (const index in this.order.lines) {
            const orderline = this.order.lines[index];
            const lineData = data[index];
            if (lineData) {
                lineData.bundle_details = (orderline?.bundleDetails?.length) ? orderline.bundleDetails : false;
            }
        }
        return data;
    },
});
