/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { qrCodeSrc } from "@point_of_sale/utils";

patch(Order.prototype, {
    export_for_printing() {
        const res = super.export_for_printing(...arguments);
        const config = this.pos.config || {};

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

        // In Odoo 17, use this.orderlines (a PosCollection)
        const jsLines = this.orderlines || [];
        res.orderlines = (res.orderlines || []).map((line, index) => {
            const enriched = { ...line };
            // PosCollection is iterable and can be indexed
            const jsLine = jsLines[index];
            const product = jsLine?.product;

            fields.forEach(f => enriched[f] = "");

            if (product) {
                fields.forEach(f => {
                    let fieldName = f;
                    // Handle Odoo 17 field naming (list_price -> lst_price)
                    if (f === 'list_price' && product.lst_price !== undefined) {
                        fieldName = 'lst_price';
                    }

                    let value = product[fieldName];
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
