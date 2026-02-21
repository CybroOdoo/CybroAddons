/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";

patch(ProductScreen.prototype, {

    setup() {
        super.setup();
        this.orm = useService("orm");
        this._loadLocationStockMap();
    },

    async _loadLocationStockMap() {
        const locationId = this.pos.res_setting.raw.stock_location_id;
        console.log(this.pos, "locationId")
        if (!locationId) return;

        const quants = await this.orm.call(
            "stock.quant",
            "search_read",
            [[["location_id", "=", locationId]]],
            { fields: ["product_id", "available_quantity"] }
        );

        console.log(quants, "quants")

        const map = {};

        quants.forEach(q => {
            const productId = q.product_id[0];
            map[productId] = (map[productId] || 0) + q.available_quantity;
        });

        this.pos.location_stock_map = map;

        console.log("POS LOCATION STOCK MAP LOADED", map);
    }
});
