    /** @odoo-module */

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { qrCodeSrc } from "@point_of_sale/utils";

patch(PosOrder.prototype, {
    get_receipt_info() {
        const res = super.get_receipt_info(...arguments);
        const config = this.config || {};



        let fields = [];
        if (config.is_custom_receipt) {
            try {
                fields = JSON.parse(config.selected_product_fields || "[]");
            } catch {
                fields = [];
            }
        }
        res.dynamic_fields = fields;
        res.custom_qr_image = this.custom_qr_image || null;
        res.custom_receipt_token = this.custom_receipt_token || null;

        const jsLines = this.lines || [];
        res.orderlines = (res.orderlines || []).map((line, index) => {
            const enriched = { ...line };
            const jsLine = jsLines[index];
            const product = jsLine?.product_id;

            fields.forEach(f => enriched[f] = "");

            if (product) {
                fields.forEach(f => {
                    let value = product[f];
                    if (value == null) value = "";
                    else if (typeof value === "object") {
                        value = value.display_name || value.name || "";
                    } else {
                        value = String(value);
                    }
                    enriched[f] = value;
                });
            }
            return enriched;
        });


        res.enable_qr = !!config.enable_qr;

        if (!res.enable_qr) {
            res.qr_src = null;
            return res;
        }

        const isDesignMode = !this.finalized;

        if (isDesignMode) {
            res.qr_src = qrCodeSrc("QR PREVIEW");
            return res;
        }

        const qrText =
            `ORDER=${this.name}` +
            `,DATE=${res.date}` +
            `,TOTAL=${this.get_total_with_tax().toFixed(2)}` +
            `,TAX=${res.amount_tax?.toFixed(2) || "0.00"}` +
            `,PAYMENT=${res.paymentlines?.[0]?.name || ""}` +
            `,ITEMS=${res.orderlines.length}`;

        res.qr_src = qrCodeSrc(qrText);

        return res;
    },
});
