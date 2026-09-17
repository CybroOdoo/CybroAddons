/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";
import { registerTemplate } from "@web/core/templates";

let currentCustomDesign = null;
let unregisterCustomTemplate = null;

patch(PosTicketPrinterPlugin.prototype, {
    async generateIframe(template, data)
    {
        try {
            if (template === "point_of_sale.pos_order_receipt") {
                const isCustomReceipt = this.config?.is_custom_receipt;
                let customDesign = this.config?.design_receipt;
                if (isCustomReceipt && customDesign) {
                    const customTemplateName = "custom_receipts_for_pos.custom_design";
                    if (currentCustomDesign !== customDesign) {
                        if (unregisterCustomTemplate) {
                            unregisterCustomTemplate();
                            unregisterCustomTemplate = null;
                        }
                        const wrappedDesign = `<html t-name="${customTemplateName}"><t t-call="point_of_sale.pos_order_receipt_style" /><div class="custom-receipt-wrapper">${customDesign}</div></html>`;
                        unregisterCustomTemplate = registerTemplate(customTemplateName, "custom_receipts_for_pos", wrappedDesign);
                        currentCustomDesign = customDesign;
                    }
                    template = customTemplateName;
                }
            }
            return await super.generateIframe(template, data);
        } catch (error) {
            console.error("ERROR IN generateIframe:", error);
            throw error;
        }
    }
});



