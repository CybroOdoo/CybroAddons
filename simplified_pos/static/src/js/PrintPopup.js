import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, signal } from "@odoo/owl";

export class PrintPopup extends Component {
    static template = "simplified_pos.PrintPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        bodyText: { type: String, optional: true },
        close: { type: Function, optional: true },
        getPayload: { type: Function, optional: true },
        id: { type: String, optional: true },
        orderToPrint: { type: Object, optional: true },
    };

    receiptRef = signal.ref();

    setup() {
        super.setup();
        this.pos = usePos();
    }
    get currentOrder() {
        return this.props.orderToPrint || (typeof this.pos?.getOrder === "function" ? this.pos.getOrder() : this.pos?.currentOrder);
    }
    finishOrder() {
        const currentOrder = typeof this.pos?.getOrder === "function" ? this.pos.getOrder() : this.pos?.currentOrder;
        if (!currentOrder || currentOrder.state === "paid") {
            if (typeof this.pos?.addNewOrder === "function") {
                this.pos.addNewOrder();
            } else if (typeof this.pos?.add_new_order === "function") {
                this.pos.add_new_order();
            }
        }
    }
    async printReceipt() {
        /* get the HTML content of the receipt using ref or selector fallback */
        var receiptEl = this.receiptRef.el || (typeof this.receiptRef === "function" && this.receiptRef()?.el) || document.querySelector('.popup-selection');
        var content = receiptEl ? receiptEl.innerHTML : '';
        if (!content) {
            if (this.props.close) {
                this.props.close();
            }
            this.finishOrder();
            return;
        }
        /* create a new window to hold the content to be printed */
        var printWindow = window.open('', 'PrintWindow', 'height=600,width=400');
        if (!printWindow) {
            if (this.props.close) {
                this.props.close();
            }
            this.finishOrder();
            return;
        }
        printWindow.document.write('<html><head><title>Print Receipt</title><style>body { font-family: sans-serif; padding: 10px; }</style></head><body>' + content + '</body></html>');
        printWindow.document.close();
        printWindow.focus();
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
            if (this.props.close) {
                this.props.close();
            }
            this.finishOrder();
        }, 250);
    }
    async cancel() {
        /*Close popup and complete order*/
        if (this.props.close) {
            this.props.close();
        }
        this.finishOrder();
    }
    get orderlines() {
        /*Selected order lines are passed to UI.*/
        const self = this;
        const order = this.currentOrder;
        if (!order) return [];
        var orderlines = order.lines || order.orderlines || (typeof order.get_orderlines === "function" ? order.get_orderlines() : []);
        var orderlinesList = [];
        orderlines.forEach(function (line) {
            var productName = line.product_id?.display_name || line.full_product_name || (typeof line.get_full_product_name === "function" ? line.get_full_product_name() : "") || line.product?.display_name || "";
            var qty = (typeof line.get_quantity === "function" ? line.get_quantity() : line.qty) || 0;
            var allPrices = typeof line.get_all_prices === "function" ? line.get_all_prices() : null;
            var rawPrice = allPrices?.priceWithTax ??
                           allPrices?.price_with_tax ??
                           (typeof line.get_price_with_tax === "function" ? line.get_price_with_tax() : null) ??
                           (typeof line.get_display_price_with_taxes === "function" ? line.get_display_price_with_taxes() : null) ??
                           (line.price_subtotal_incl || null) ??
                           (typeof line.get_display_price === "function" ? line.get_display_price() : null) ??
                           line.price_subtotal ?? 0;
            var formattedPrice = typeof self.pos?.format_currency === "function" ? self.pos.format_currency(rawPrice) : rawPrice.toFixed(2);
            orderlinesList.push([productName, qty, rawPrice, formattedPrice]);
        });
        return orderlinesList;
    }
    get total() {
        /*Total is calculated and passed*/
        var order = this.currentOrder;
        if (!order) return "0.00";
        var rawTotal = (typeof order.get_total_with_tax === "function" ? order.get_total_with_tax() : null) ??
                       (typeof order.get_total === "function" ? order.get_total() : null) ??
                       order.amount_total ?? 0;
        if (!rawTotal && (order.payment_ids?.length || order.paymentlines?.length)) {
            var totalvalues = order.payment_ids || order.paymentlines || [];
            totalvalues.forEach(function (payment) {
                rawTotal += (payment.amount || (typeof payment.get_amount === "function" ? payment.get_amount() : 0));
            });
        }
        return typeof this.pos?.format_currency === "function" ? this.pos.format_currency(rawTotal) : rawTotal.toFixed(2);
    }
    get cashierName() {
        const cashier = typeof this.pos?.get_cashier === "function" ? this.pos.get_cashier() : (this.pos?.cashier || this.pos?.user);
        return cashier?.name || "";
    }
}
