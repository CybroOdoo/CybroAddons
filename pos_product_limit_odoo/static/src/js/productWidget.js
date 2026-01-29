/** @odoo-module */
import ProductsWidget from 'point_of_sale.ProductsWidget';
import Registries from 'point_of_sale.Registries';

export const ProductsWidgetLimit =(ProductsWidget)=>
    class ProductsWidgetLimit extends ProductsWidget{
        get productsToDisplay() {
            let list = [];
            if (this.searchWord !== '') {
                list = this.env.pos.db.search_product_in_category(
                    this.selectedCategoryId,
                    this.searchWord
                );
            } else {
                list = this.env.pos.db.get_product_by_category(this.selectedCategoryId);
            }
            let all_items = list.sort(function (a, b) { return a.display_name.localeCompare(b.display_name) });
            let limit_items = all_items
            if (this.env.pos.config.product_limit <= 0){
                limit_items = all_items;
            }
            else{
                limit_items = all_items.slice(0,this.env.pos.config.product_limit);
            }

            return limit_items;
        }

    }

Registries.Component.extend(ProductsWidget,ProductsWidgetLimit);