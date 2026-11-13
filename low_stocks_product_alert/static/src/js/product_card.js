/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";

patch(ProductCard.prototype, {
    setup() {
        if (super.setup) {
            super.setup(...arguments);
        }
        try {
            this.pos = usePos();
        } catch (_) {
            this.pos = null;
        }
    },

    get displayStockAlert() {
        const product = this.props?.product;
        if (!product) {
            return false;
        }
        if (product.alert_state !== undefined && product.alert_state !== null) {
            return Boolean(product.alert_state);
        }
        if (product.alert_tag !== undefined && product.alert_tag !== false && product.alert_tag !== null && product.alert_tag !== "") {
            return true;
        }
        return false;
    },

    get displayStock() {
        if (this.displayStockAlert) {
            return false;
        }
        return super.displayStock !== undefined ? super.displayStock : true;
    },

    get productStockQty() {
        const product = this.props?.product;
        if (!product) {
            return 0;
        }
        if (product.alert_tag !== undefined && product.alert_tag !== false && product.alert_tag !== null && product.alert_tag !== "") {
            const parsedTag = parseFloat(product.alert_tag);
            if (!isNaN(parsedTag)) {
                return parsedTag % 1 === 0 ? Math.round(parsedTag) : parsedTag;
            }
        }
        let qty = null;
        const pos = this.pos || this.env?.services?.pos;
        if (pos && typeof pos.getProductStockQty === "function") {
            qty = pos.getProductStockQty(product);
        }
        if (qty === null || qty === undefined || qty === false) {
            qty = product.qty_available ?? 0;
        }
        if (typeof qty === "string") {
            const parsed = parseFloat(qty);
            if (!isNaN(parsed)) {
                qty = parsed;
            }
        }
        if (typeof qty === "number" && !isNaN(qty)) {
            return qty % 1 === 0 ? Math.round(qty) : qty;
        }
        return 0;
    },
});
