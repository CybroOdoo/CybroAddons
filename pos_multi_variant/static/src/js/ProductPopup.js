/** @odoo-module **/

import Registries from 'point_of_sale.Registries';
import { useListener } from "@web/core/utils/hooks";
const ProductItem = require('point_of_sale.ProductItem');
const { useState } = owl;


class ProductsPopup extends ProductItem {
    setup() {
        super.setup();
        this.state = useState({
            variant_details: this.props.variant_details,
            selected_variants: {},
            price_total: {},
        })
    }

    SelectVariant(product,variant) {
        if (this.state.selected_variants[product.attribute_id[1]] === variant.id){
            this.state.selected_variants[product.attribute_id[1]] = false
            this.state.price_total[product.attribute_id[1]] = 0.0
        }
        else{
            this.state.selected_variants[product.attribute_id[1]] = variant.id
            this.state.price_total[product.attribute_id[1]] = product.extra_price
        }
    }

    clickConfirm(e){
        const total = Object.values(this.state.price_total).reduce((sum, value) => sum + value, 0);
        var order = this.env.pos.get_order()
        var selected_orderline = order.get_selected_orderline()
        selected_orderline.price += total
          this.env.posbus.trigger('close-popup', {
            popupId: this.props.id
           });
    }
    clickCancel(){
        this.env.pos.get_order().orderlines.remove(this.env.pos.get_order().selected_orderline)
        this.env.posbus.trigger('close-popup', {
            popupId: this.props.id
        });
    }

    imageUrl() {
        return `/web/image?model=product.product&field=image_1920&id=${this.props.product_tmpl_id}&unique=1`;
    }

    getSelected(attr, variant) {
         return this.state.selected_variants[attr] === variant.id
    }

}
ProductsPopup.template = 'ProductsPopUp';
ProductsPopup.defaultProps = {};
Registries.Component.add(ProductsPopup);
