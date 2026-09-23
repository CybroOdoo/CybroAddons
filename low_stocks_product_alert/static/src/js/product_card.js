/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    get displayStockAlert() {
        if (!this.props.product) {
            return false;
        }
        if (this.props.product.alert_state !== undefined && this.props.product.alert_state !== null) {
            return Boolean(this.props.product.alert_state);
        }
        if (this.props.product.alert_tag !== undefined && this.props.product.alert_tag !== false && this.props.product.alert_tag !== null && this.props.product.alert_tag !== "") {
            return true;
        }
        const qty = this.productStockQty;
        const limit = this.pos?.config?.min_low_stock_alert ?? 50;
        return typeof qty === "number" && qty <= limit;
    },

    get displayStock() {
        if (this.displayStockAlert) {
            return false;
        }
        return super.displayStock !== undefined ? super.displayStock : true;
    },

    get productStockQty() {
        if (!this.props.product) {
            return 0;
        }
        if (this.props.product.alert_tag !== undefined && this.props.product.alert_tag !== false && this.props.product.alert_tag !== null && this.props.product.alert_tag !== "") {
            const parsedTag = parseFloat(this.props.product.alert_tag);
            if (!isNaN(parsedTag)) {
                return parsedTag % 1 === 0 ? Math.round(parsedTag) : parsedTag;
            }
        }
        let qty = null;
        if (this.pos && typeof this.pos.getProductStockQty === "function") {
            qty = this.pos.getProductStockQty(this.props.product);
        }
        if (qty === null || qty === undefined || qty === false) {
            qty = this.props.product.qty_available ?? 0;
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
