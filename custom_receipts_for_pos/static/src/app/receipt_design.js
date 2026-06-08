/** @odoo-module */
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { Component, xml } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    get templateProps() {
        const order = this.props.order;
        let receiptData = {
            headerData: this.props.receipt?.headerData || {},
        };
        try {
            Object.assign(receiptData, {
                name: order?.name || '',
                date: (() => {
                    let rawDate = order?.date_order || order?.validation_date || this.props.receipt?.date || '';
                    if (rawDate && typeof rawDate === 'object' && typeof rawDate.toFormat === 'function') {
                        return rawDate.toFormat('dd/MM/yyyy HH:mm:ss');
                    }
                    const sDate = String(rawDate || '').replace('T', ' ').split('.')[0];
                    if (sDate.includes('-')) {
                        const parts = sDate.split(' ');
                        const dParts = parts[0].split('-');
                        if (dParts.length === 3) {
                            return `${dParts[2]}/${dParts[1]}/${dParts[0]}${parts[1] ? ' ' + parts[1] : ''}`;
                        }
                    }
                    return sDate;
                })(),
                headerData: receiptData.headerData || this.header || {},
                change: order?.change || 0,
                amount_total: order?.priceIncl || 0,
                total_with_tax: order?.priceIncl || 0,
                total_without_tax: order?.priceExcl || 0,
                total_tax: order?.amountTaxes || 0,
                total_discount: order?.getTotalDiscount?.() || 0,
                tax_details: order?.prices?.taxDetails?.subtotals?.[0]?.tax_groups || [],
                footer: order?.config?.receipt_footer || '',
                footer_html: order?.config?.receipt_footer || '',
            });
        } catch (e) {
            console.warn('Custom receipt: error building receipt data', e);
        }
        // Pre-process orderlines into plain objects so they work
        // reliably inside dynamically compiled OWL xml templates
        const formatCurrency = this.env?.utils?.formatCurrency || ((v) => String(v));
        const orderlines = [];
        try {
            for (const line of (order?.lines || [])) {
                orderlines.push({
                    productName: line.getFullProductName?.() || line.full_product_name || line.product_id?.display_name || '',
                    qty: line.qty || 0,
                    discount: line.discount || 0,
                    customerNote: line.getCustomerNote?.() || line.customer_note || '',
                    priceIncl: line.priceIncl || 0,
                    formattedPriceIncl: formatCurrency(line.priceIncl || 0),
                });
            }
        } catch (e) {
            console.warn('Custom receipt: error building orderlines', e);
        }
        // Pre-process payment lines into plain objects
        const paymentlines = [];
        try {
            for (const line of (order?.payment_ids || [])) {
                paymentlines.push({
                    name: line.payment_method_id?.name || '',
                    amount: line.amount || 0,
                    formattedAmount: formatCurrency(line.amount || 0),
                    ticket: line.ticket || '',
                });
            }
        } catch (e) {
            console.warn('Custom receipt: error building paymentlines', e);
        }
        return {
            order: order,
            orderlines: orderlines,
            paymentlines: paymentlines,
            receipt: receiptData,
            data: receiptData,
        };
    },
    get templateComponent() {
        var mainRef = this;
        return class extends Component {
            setup() { }
            static template = xml`${mainRef.pos.config.design_receipt}`
        };
    },
    get isTrue() {
        return !!this.pos.config.is_custom_receipt;
    }
});
