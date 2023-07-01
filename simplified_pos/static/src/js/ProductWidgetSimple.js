odoo.define('point_of_sale.ProductsWidgetSimple', function (require) {
    'use strict';
    const Registries = require('point_of_sale.Registries');
    const ProductsWidget = require('point_of_sale.ProductsWidget');
    const ProductsWidgetSimple = (ProductsWidget) =>
        class extends ProductsWidget {
            setup() {
                super.setup();
            }
            get productsToDisplay() {
                /* This function is override to remove products showing before hand.*/
                let list = [];
                if (this.searchWord !== '') {
                    list = this.env.pos.db.search_product_in_category(
                        this.selectedCategoryId,
                        this.searchWord
                    );
                }
                return list.sort(function (a, b) { return a.display_name.localeCompare(b.display_name) });
            }
        };
    Registries.Component.extend(ProductsWidget, ProductsWidgetSimple);
    return ProductsWidgetSimple;
});