/** @odoo-module **/
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, Component, xml } from "@odoo/owl";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
        this.notification = useService("notification");
        this.state = useState({ template: true });
    },

    sanitizeReceiptXml(xmlString) {
        const parser = new DOMParser();
        const parsed = parser.parseFromString(xmlString, "text/html");
        let html = parsed.body.innerHTML
            .replace(/<br\s*>/gi, "<br/>")
            .replace(/<hr\s*>/gi, "<hr/>")
            .replace(/&nbsp;|\u00A0/g, " ")
            .replace(/<img([^>]*)>/gi, "<img$1/>")
            .replace(/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;)/g, "&amp;")
            .trim();
        const font = this.pos.config.design_receipt_font_style || "Arial";
        html = html.replace(/<div([^>]*class="pos-receipt"[^>]*)>/i,
            (m, attrs) =>
                `<div ${attrs.replace(/\s*style="[^"]*"/gi, "")} style="font-family:${font};">`
        );
        const order = this.pos.get_order();
        const receipt = order.export_for_printing();
        const partner = order.get_partner();
        const company = this.pos.company
        html = html
        .replaceAll('[[ receipt.total_without_tax ]]',
            this.env.utils.formatCurrency(receipt.total_without_tax || 0))
        .replaceAll('[[ receipt.amount_total ]]',
            this.env.utils.formatCurrency(receipt.amount_total || 0))
        const replaced = html.replace(
            /\[\[\s*([\w.\s]+)\s*\]\]/g,
            (match, fieldPath) => {
                const path = fieldPath.trim().replace(/\s+/g, "");
                let value = "";
                const split_path = path.split(".");
                const model = split_path[0];
                const field = split_path.slice(1);
                if (path.startsWith("order.")) {
                    value = order?.[path.slice(6)];
                }
                else if (path.startsWith("partner.")) {
                    value = partner?.[path.slice(8)];
                }
                else if (path.startsWith("company.")) {
                    value = company?.[path.slice(8)];
                }
                return value ? value : "";
            }
        );
        return replaced;
    },

    get templateProps() {
        const order = this.pos.get_order();
        const receipt = order.export_for_printing();
        return {
            data: this.props.data,
            order,
            receipt,
            orderlines: this.props.data.orderlines,
            paymentlines: receipt.paymentlines,
        };
    },

    get templateComponent() {
        const design = this.pos.config?.design_receipt || "";
        const xmlString = this.sanitizeReceiptXml(design);
        return class extends Component {
            static template = xml`${xmlString}`;
        };
    },

    get isFalse() {
        return !this.pos.config.is_custom_receipt;
    },
});

