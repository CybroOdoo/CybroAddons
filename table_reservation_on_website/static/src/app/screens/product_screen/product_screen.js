/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

patch(ProductScreen.prototype, {
    // Override the bookTable function for displaying and booking of tables
    bookTable() {
        this.pos.showScreen("ReservationsScreen");
    },
});
