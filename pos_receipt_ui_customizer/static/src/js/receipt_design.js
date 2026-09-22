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

            const order = this.props?.order || this.order || (this.pos && this.pos.get_order && this.pos.get_order());
            if (!order) return "";

            let receipt;
            try {
                receipt = typeof order.export_for_printing === 'function' ? order.export_for_printing() : null;
            } catch (e) {
                console.warn("export_for_printing is unavailable on order, applying fallback.", e);
            }
            if (!receipt) {
                receipt = {
                    total_without_tax: order.getTotalWithoutTax ? order.getTotalWithoutTax() : 0,
                    amount_total: order.getTotalWithTax ? order.getTotalWithTax() : 0,
                    qr_src: this.qrCode || this.props?.receipt?.qr_src,
                    custom_qr_image: order.custom_qr_image || null,
                    custom_receipt_token: order.custom_receipt_token || null
                };
            }

            const partner = order?.getPartner?.() || order?.partner_id || order?.get_partner?.();
            const company = order?.company || this.pos?.company;

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
                .replace(/props\.data\.custom_qr_image/g, "props.receipt.custom_qr_image")
                .trim();

            const font = this.pos.config?.design_receipt_font_style || "Arial";
            html = html.replace(/<div([^>]*class="pos-receipt"[^>]*)>/i,
                (m, attrs) =>
                    `<div ${attrs.replace(/\s*style="[^"]*"/gi, "")} style="font-family:${font};">`
            );

            const formatCurrencyFallback = (amount) => {
                if (this.formatCurrency) return this.formatCurrency(amount);
                if (this.env?.utils?.formatCurrency) return this.env.utils.formatCurrency(amount);
                return amount;
            };

            html = html
                .replaceAll('[[ receipt.total_without_tax ]]',
                    formatCurrencyFallback(receipt.total_without_tax || 0))
                .replaceAll('[[ receipt.amount_total ]]',
                    formatCurrencyFallback(receipt.amount_total || 0));

            const replaced = html.replace(
                /\[\[\s*([\w.\s]+)\s*\]\]/g,
                (match, fieldPath) => {
                    const path = fieldPath.trim().replace(/\s+/g, "");
                    let value = "";
                    if (path.startsWith("order.")) {
                        value = order?.[path.slice(6)];
                    } else if (path.startsWith("partner.")) {
                        value = partner?.[path.slice(8)];
                    } else if (path.startsWith("company.")) {
                        value = company?.[path.slice(8)];
                    }
                    return (value !== false && value !== null && value !== undefined) ? value : match;
                }
            );

            return replaced;
        } catch (error) {
            console.error("Error sanitizing receipt XML:", error);
            return "";
        }
    },


    _getTaxIncludedAmount(jsLine) {
        if (!jsLine) return 0;

        if (jsLine.allPrices?.priceWithTax !== undefined) {
            return jsLine.allPrices.priceWithTax;
        }
        if (typeof jsLine.getPriceWithTax === 'function') {
            return jsLine.getPriceWithTax();
        }
        if (typeof jsLine.getDisplayPrice === 'function') {
            return jsLine.getDisplayPrice();
        }
        if (typeof jsLine.get_price_with_tax === 'function') {
            return jsLine.get_price_with_tax();
        }
        if (typeof jsLine.price_with_tax === 'number') {
            return jsLine.price_with_tax;
        }

        const qty = jsLine.getQuantity?.() ?? jsLine.get_quantity?.() ?? jsLine.qty ?? jsLine.quantity ?? 1;
        const unitPrice = parseFloat(
            jsLine.getUnitPrice?.() ?? jsLine.price_unit ?? jsLine.lst_price ?? jsLine.product_id?.lst_price ?? 0
        ) || 0;

        let tax = 0;
        if (typeof jsLine.getTax === 'function') {
            tax = jsLine.getTax();
        } else if (typeof jsLine.get_tax === 'function') {
            tax = jsLine.get_tax();
        } else if (typeof jsLine.tax === 'number') {
            tax = jsLine.tax;
        }

        return (unitPrice * qty) + tax;
    },

    get templateProps() {
        const order = this.props?.order || this.order || (this.pos && this.pos.get_order && this.pos.get_order());

        if (!order) {
            return {
                data: this.props.data || {},
                order: null,
                receipt: {},
                orderlines: [],
                paymentlines: [],
                dynamic_fields: [],
            };
        }

        const formatP = (amount) => {
            if (this.formatCurrency) return this.formatCurrency(amount);
            if (this.env?.utils?.formatCurrency) return this.env.utils.formatCurrency(amount);
            return amount;
        };

        const jsOrderlines = order.lines || order.get_orderlines?.() || [];

        let receipt;
        try {
            receipt = typeof order.export_for_printing === 'function' ? order.export_for_printing() : null;
        } catch (e) {
            console.warn("export_for_printing is unavailable on order, applying fallback.");
        }

        if (!receipt) {
            receipt = {
                dynamic_fields: order.dynamic_fields || [],
                orderlines: jsOrderlines.map(line => {
                    const taxIncludedAmount = this._getTaxIncludedAmount(line);
                    const qty = line.get_quantity?.() ?? line.qty ?? line.quantity ?? 1;
                    return {
                        ...line,
                        cid: line.uuid || line.id || line.cid,
                        product_id: line.product_id?.id || line.product?.id || line.get_product?.()?.id,
                        productName: line.get_full_product_name?.() || line.full_product_name || line.product?.display_name || line.product?.name || "Unknown Product",
                        qty,
                        _taxIncludedAmount: taxIncludedAmount,
                        price: formatP(taxIncludedAmount),
                        price_display: formatP(taxIncludedAmount),
                    };
                }),
                paymentlines: order.payment_ids || order.get_paymentlines?.() || [],
                qr_src: this.qrCode || this.props?.receipt?.qr_src,
                custom_qr_image: order.custom_qr_image || null,
                custom_receipt_token: order.custom_receipt_token || null,
                total_without_tax: order.getTotalWithoutTax ? order.getTotalWithoutTax() : 0,
                amount_total: order.getTotalWithTax ? order.getTotalWithTax() : 0,
            };

            const config = this.pos?.config || order.config || {};
            let fields = [];
            if (config.is_custom_receipt) {
                try { fields = JSON.parse(config.selected_product_fields || "[]"); } catch { fields = []; }
            }
            receipt.dynamic_fields = fields;

            if (config.enable_qr) {
                const isDesignMode = !order.finalized;
                if (isDesignMode) {
                    if (this.env?.services?.pos?.qrCodeSrc) {
                        receipt.qr_src = this.env.services.pos.qrCodeSrc("QR PREVIEW");
                    }
                } else {
                    const qrText =
                        `ORDER=${order.name || ""}` +
                        `,DATE=${order.date_order || ""}` +
                        `,TOTAL=${(order.getTotalWithTax ? order.getTotalWithTax() : 0).toFixed(2)}` +
                        `,TAX=${(order.getTotalTax ? order.getTotalTax() : 0).toFixed(2)}` +
                        `,PAYMENT=${receipt.paymentlines?.[0]?.name || ""}` +
                        `,ITEMS=${receipt.orderlines.length}`;
                    if (this.env?.services?.pos?.qrCodeSrc) {
                        receipt.qr_src = this.env.services.pos.qrCodeSrc(qrText);
                    }
                }
            }
        } else {

            if (receipt.orderlines) {
                receipt.orderlines = receipt.orderlines.map(receiptLine => {
                    const jsLine = jsOrderlines.find(ol =>
                        ol.cid === receiptLine.cid ||
                        ol.uuid === receiptLine.cid ||
                        ol.id === receiptLine.cid ||
                        (receiptLine.product_id && (
                            ol.product?.id === receiptLine.product_id ||
                            ol.product_id?.id === receiptLine.product_id
                        ))
                    );

                    if (jsLine) {
                        const taxIncludedAmount = this._getTaxIncludedAmount(jsLine);
                        return {
                            ...receiptLine,
                            _taxIncludedAmount: taxIncludedAmount,
                            price: formatP(taxIncludedAmount),
                            price_display: formatP(taxIncludedAmount),
                        };
                    }
                    return receiptLine;
                });
            }
        }


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

        const orderlines = (receipt.orderlines || []).map(line => {
            let currentOrderline = jsOrderlines.find(ol =>
                ol.cid === line.cid || ol.uuid === line.cid || ol.id === line.cid
            );
            if (!currentOrderline && line.product_id) {
                currentOrderline = jsOrderlines.find(ol =>
                    ol.product?.id === line.product_id || ol.product_id?.id === line.product_id
                );
            }

            const product = currentOrderline?.product || currentOrderline?.product_id ||
                currentOrderline?.get_product?.() ||
                this.pos.db?.get_product_by_id?.(line.product_id) || line.product;

            const dynamicValues = {};
            dynamicFields.forEach(field => {
                dynamicValues[field] = line[field] || currentOrderline?.[field] || product?.[field] || '';
            });

            let finalPrice = line.price;
            if (line._taxIncludedAmount !== undefined) {
                finalPrice = formatP(line._taxIncludedAmount);
            } else if (currentOrderline) {
                finalPrice = formatP(this._getTaxIncludedAmount(currentOrderline));
            }

            return {
                ...line,
                product,
                _dynamicValues: dynamicValues,
                price: finalPrice,
                price_display: finalPrice,
            };
        });

        return {
            data: this.props.data || {},
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
                            const flexMap = { left: 'flex-start', center: 'center', right: 'flex-end' };
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
                            if (wrapper) {
                                wrapper.parentNode.insertBefore(qrArea, wrapper);
                            } else {
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
                            if (!config.enable_qr_section) {
                                qrArea.style.display = "none";
                            } else {
                                qrArea.style.display = "flex";
                                const position = config.qr_position || 'center';
                                const flexMap = { left: 'flex-start', center: 'center', right: 'flex-end' };
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
        const isCustom = config.is_custom_receipt;
        const design = config.design_receipt;
        return !isCustom || !design || !design.trim();
    },
});