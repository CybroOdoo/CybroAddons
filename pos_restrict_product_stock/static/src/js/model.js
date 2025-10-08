/** @odoo-module **/

import Registries from 'point_of_sale.Registries';
import { Product } from 'point_of_sale.models';

const RestrictProduct = (Product) => class RestrictProduct extends Product {
    setQty(qty) {
        if (this.detailed_type !== 'service' &&
            this.pos.config.is_display_stock &&
            this.pos.company.point_of_sale_update_stock_quantities == 'real') {
            this.qty_available -= qty;
            this.virtual_available -= qty;
        }
    }
}

Registries.Model.extend(Product, RestrictProduct);

