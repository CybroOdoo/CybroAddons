/** @odoo-module **/
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, Component, xml, useRef, onMounted } from "@odoo/owl";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();
        this.pos = useService("pos");
        this.notification = useService("notification");
        this.state = useState({ template: true });
    },

    sanitizeReceiptXml(xmlString) {
        if (!xmlString) return "";
        try {
            const parser = new DOMParser();
            const parsed = parser.parseFromString(xmlString, "text/html");

            const order = this.pos.get_order();
            const receipt = order?.export_for_printing?.() || {};
            const partner = order?.get_partner?.();
            const company = this.pos.company;

            const selectedFieldsStr = this.pos.config?.selected_product_fields || "[]";
            let selectedFields = [];
            try {
                selectedFields = JSON.parse(selectedFieldsStr);
            } catch (e) {
                selectedFields = [];
            }

            if (selectedFields.length > 0) {
                const table = parsed.querySelector(".receipt-table");
                const headerRow = table?.querySelector("thead tr");
                if (headerRow) {
                    selectedFields.forEach(field => {
                        if (!headerRow.querySelector(`th[data-field="${field}"]`)) {
                            const th = document.createElement("th");
                            th.setAttribute("data-field", field);
                            th.style.textAlign = "center";
                            th.style.fontSize = "12px";
                            th.style.padding = "4px";
                            th.textContent = field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                            headerRow.appendChild(th);
                        }
                    });
                }
            }

            let html = parsed.body.innerHTML
                .replace(/<br\s*>/gi, "<br/>")
                .replace(/<hr\s*>/gi, "<hr/>")
                .replace(/&nbsp;|\u00A0/g, " ")
                .replace(/<img([^>]*)>/gi, "<img$1/>")
                .replace(/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;)/g, "&amp;")
                .trim();

            const font = this.pos.config?.design_receipt_font_style || "Arial";
            html = html.replace(/<div([^>]*class="pos-receipt"[^>]*)>/i,
                (m, attrs) =>
                    `<div ${attrs.replace(/\s*style="[^"]*"/gi, "")} style="font-family:${font};" t-ref="root">`
            );

            html = html
                .replaceAll('[[ receipt.total_without_tax ]]',
                    this.env.utils.formatCurrency(receipt.total_without_tax || 0))
                .replaceAll('[[ receipt.amount_total ]]',
                    this.env.utils.formatCurrency(receipt.amount_total || 0));

            // Case-insensitive placeholder replacement
            const replaced = html.replace(
                /\[\[\s*([\w.\s]+)\s*\]\]/gi,
                (match, fieldPath) => {
                    const path = fieldPath.trim().replace(/\s+/g, "").toLowerCase();
                    let value = "";

                    if (path.startsWith("order.")) {
                        value = order?.[path.slice(6)];
                    } else if (path.startsWith("partner.")) {
                        value = partner?.[path.slice(8)] || order?.get_partner()?.[path.slice(8)];
                    } else if (path.startsWith("company.")) {
                        value = company?.[path.slice(8)];
                    } else if (path.startsWith("receipt.")) {
                        value = receipt?.[path.slice(8)];
                    }

                    return (value !== false && value !== null && value !== undefined) ? value : "";
                }
            );

            return replaced;
        } catch (error) {
            console.error("Error sanitizing receipt XML:", error);
            return "";
        }
    },

    get templateProps() {
        const order = this.pos.get_order();

        if (!order) {
            return {
                data: this.props.data,
                order: null,
                receipt: {},
                orderlines: [],
                paymentlines: [],
                dynamic_fields: [],
            };
        }

        const receipt = order.export_for_printing();
        const dynamicFields = [
            ...new Set(
                (receipt.dynamic_fields || [])
                    .map(f => {
                        if (typeof f === 'string') return f.trim();
                        if (typeof f === 'object' && f.name) return f.name.trim();
                        return null;
                    })
                    .filter(Boolean)
            )
        ];

        const jsOrderlines = order.get_orderlines() || [];
        const orderlines = (receipt.orderlines || []).map(line => {
            let currentOrderline = jsOrderlines.find(ol => ol.cid === line.cid);

            if (!currentOrderline && line.product_id) {
                currentOrderline = jsOrderlines.find(ol => ol.product?.id === line.product_id);
            }

            const product = currentOrderline?.product || this.pos.db.get_product_by_id(line.product_id);

            const dynamicValues = {};
            dynamicFields.forEach(field => {
                // Check multiple sources for the dynamic field value
                let val = line[field] || currentOrderline?.[field] || product?.[field];

                // Fallback for Odoo 17 field names
                if (!val && field === 'list_price') {
                    val = line['lst_price'] || currentOrderline?.['lst_price'] || product?.['lst_price'];
                }

                dynamicValues[field] = val || '';
            });

            return {
                ...line,
                product,
                _dynamicValues: dynamicValues,
            };
        });

        return {
            data: this.props.data,
            order,
            receipt,
            orderlines,
            paymentlines: receipt.paymentlines || [],
            dynamic_fields: dynamicFields,
        };
    },

    get templateComponent() {
        try {
            const design = this.pos.config?.design_receipt || "";
            if (!design) return null;

            const xmlString = this.sanitizeReceiptXml(design);
            if (!xmlString) return null;

            return class extends Component {
                static template = xml`${xmlString}`;
                static props = {
                    data: { type: Object, optional: true },
                    order: { type: Object, optional: true },
                    receipt: { type: Object, optional: true },
                    orderlines: { type: Array, optional: true },
                    paymentlines: { type: Array, optional: true },
                    dynamic_fields: { type: Array, optional: true },
                };

                setup() {
                    this.root = useRef("root");
                    this.pos = useService("pos");

                    onMounted(() => {
                        const el = this.root.el;
                        if (!el) return;

                        const config = this.pos.config || {};
                        let fullQrContainer = el.querySelector(".receipt-qr-placeholder") || el.querySelector("#receipt_dynamic_qr");
                        let wrapper = el.querySelector(".receipt-qr-wrapper");

                        if (config.enable_qr && !wrapper) {
                            wrapper = document.createElement("div");
                            wrapper.className = "receipt-qr-wrapper";
                            const footer = el.querySelector(".before-footer");
                            if (footer) {
                                footer.parentNode.insertBefore(wrapper, footer);
                            } else {
                                const lastDiv = el.querySelector("div:last-child");
                                if (lastDiv) lastDiv.parentNode.insertBefore(wrapper, lastDiv);
                                else el.appendChild(wrapper);
                            }
                        }

                        if (config.enable_qr && wrapper && !fullQrContainer) {
                            fullQrContainer = document.createElement("div");
                            fullQrContainer.className = "receipt-qr-placeholder";
                            fullQrContainer.style.display = "flex";
                            fullQrContainer.style.marginTop = "10px";
                            wrapper.appendChild(fullQrContainer);
                        }

                        if (config.enable_qr && fullQrContainer && this.props.receipt.qr_src) {
                            fullQrContainer.style.display = "flex";
                            const position = config.receipt_qr_position || 'center';
                            const flexMap = { 'left': 'flex-start', 'center': 'center', 'right': 'flex-end' };
                            fullQrContainer.style.justifyContent = flexMap[position];
                            fullQrContainer.innerHTML = "";
                            const img = document.createElement("img");
                            img.src = this.props.receipt.qr_src;
                            const size = config.receipt_qr_size || 120;
                            img.style.width = `${size}px`;
                            img.style.height = `${size}px`;
                            fullQrContainer.appendChild(img);
                        } else if (fullQrContainer && !config.enable_qr) {
                            fullQrContainer.style.display = "none";
                        }

                        let qrArea = el.querySelector(".qrArea");
                        if (config.enable_qr_section && !qrArea) {
                            qrArea = document.createElement("div");
                            qrArea.className = "qrArea";
                            qrArea.style.display = "flex";
                            qrArea.style.justifyContent = "center";
                            qrArea.style.margin = "25px 0";
                            if (wrapper) wrapper.parentNode.insertBefore(qrArea, wrapper);
                            else {
                                const footer = el.querySelector(".before-footer");
                                if (footer) footer.parentNode.insertBefore(qrArea, footer);
                                else {
                                    const lastDiv = el.querySelector("div:last-child");
                                    if (lastDiv) lastDiv.parentNode.insertBefore(qrArea, lastDiv);
                                    else el.appendChild(qrArea);
                                }
                            }
                        }

                        if (qrArea) {
                            if (!config.enable_qr_section) qrArea.style.display = "none";
                            else {
                                qrArea.style.display = "flex";
                                const position = config.qr_position || 'center';
                                const flexMap = { 'left': 'flex-start', 'center': 'center', 'right': 'flex-end' };
                                qrArea.style.justifyContent = flexMap[position];
                            }
                        }
                    });
                }
            };
        } catch (error) {
            console.error("Error creating receipt component:", error);
            return null;
        }
    },

    get isFalse() {
        const config = this.pos.config;
        if (!config) return true;
        return !config.is_custom_receipt || !config.design_receipt || !config.design_receipt.trim();
    },
});