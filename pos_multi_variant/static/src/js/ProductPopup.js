odoo.define('pos_multi_variant.ProductsPopup', function(require) {
    'use strict';
     /* This JavaScript code defines the ProductsPopup component, which extends
     * the ProductItem class from the point_of_sale module. It represents a popup
     * for selecting product variants.
     */
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const ProductItem = require('point_of_sale.ProductItem');

    class ProductsPopup extends ProductItem {
        setup() {
            super.setup();
            useListener('click','.confirm', this.click_confirm);
            useListener('click','.product', this.select_variant);
            useListener('click','.cancel', this.click_cancel);
        }
        select_variant(e) {
            var order = this.env.pos.get_order()
            var self = e.composedPath ? e.composedPath()[2] : e.path[2];
            var action = $(self).find('.action').text();
            var category = $(self).find('.action').data('category');
            $('.product-img').find('.variant-selected').each(function ()
            {   if($(this).data('category') ==  category)
                {   $(this).text("").removeClass('variant-selected');
                    $(self).find('.action').text("Selected").addClass('variant-selected');
                }
            });
            $(self).find('.action').text("Selected").addClass('variant-selected');
            var add = $(self).find('.extra-price').text().substr(1).slice(0, -2);
            var type = $(self).find('.variants').text();
            $(self).find('.variant-selected').attr('data-price', add);
            $(self).find('.variant-selected').attr('data-type', type);
        }
        click_confirm(e){
            var price = 0.00
            var order = this.env.pos.get_order()
            var selected_orderline = order.get_selected_orderline()
            var variants = []
            this.env.pos.selectedOrder.selected_orderline.product_variants=variants
            $('.product-img').find('.variant-selected').each(function ()
            {
            var add = this.previousSibling.innerHTML;
            add = add.slice(3)
            price += parseFloat(add)
                if (order.selected_orderline.product.is_pos_variants){
                    variants.push({
                        'extra_price': add,
                        'type': $(this).data('type'),
                    })
                };
            })
            selected_orderline.price_manually_set = true;
            selected_orderline.price += price
              this.env.posbus.trigger('close-popup', {
                popupId: this.props.id
               });
        }
        click_cancel(){
             this.env.posbus.trigger('close-popup', {
                popupId: this.props.id
               });
        }
        imageUrl() {
            return `/web/image?model=product.product&field=image_1920&id=${this.props.product_tmpl_id}&unique=1`;
        }
        async _clickProduct(event) {
        }
    }
    ProductsPopup.template = 'ProductsPopUp';
    ProductsPopup.defaultProps = {};
    Registries.Component.add(ProductsPopup);
    return ProductsPopup;
});

