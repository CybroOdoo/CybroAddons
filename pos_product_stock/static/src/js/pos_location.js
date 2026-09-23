/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    get displayStock() {
        if (!this.props.product) {
            return false;
        }
        return Boolean(this.pos?.config?.display_stock_setting || this.pos?.config?.display_stock || true);
    },

    get productStockQty() {
        if (!this.props.product) {
            return 0;
        }
        return this.pos ? this.pos.getProductStockQty(this.props.product) : 0;
    },
});
