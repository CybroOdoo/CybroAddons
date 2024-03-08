/** @odoo-module */
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { patch } from "@web/core/utils/patch";

patch(ProductsWidget.prototype, {
        get productsToDisplay() {
             const { db } = this.pos;
        let list = [];
        if (this.searchWord !== "") {
            list = db.search_product_in_category(this.selectedCategoryId, this.searchWord);
        } else {
            list = db.get_product_by_category(this.selectedCategoryId);
        }
        list = list.filter((product) => !this.getProductListToNotDisplay().includes(product.id));
        let all_items = list.sort(function (a, b) {
            return a.display_name.localeCompare(b.display_name);
        });

            let limit_items = all_items
            if (this.env.services.pos.config.product_limit <= 0){
                limit_items = all_items;
            }
            else{
                limit_items = all_items.slice(0,this.env.services.pos.config.product_limit);
            }

            return limit_items;
        },

    });
