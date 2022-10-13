odoo.define('pos_multi_variant.ProductsPopup', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const { configureGui } = require('point_of_sale.Gui');
    const {
        useListener
    } = require('web.custom_hooks');
    const ProductItem = require('point_of_sale.ProductItem');
    var models = require('point_of_sale.models');



    class ProductsPopup extends ProductItem {
        constructor() {
            super(...arguments);
            useListener('click-product', this._clickProduct);
        }
        select_variant(e){
            var order = this.env.pos.get('selectedOrder')
            var self = e.currentTarget
            var action = $(self).find('.action').text();
            var categories = []
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

        click_confirm(e)
        {   var price = 0.00
            var order = this.env.pos.get_order()
            var selected_orderline = order.get_selected_orderline()
            var variant = order.selected_orderline.product_variants
            $('.product-img').find('.variant-selected').each(function ()
            {
            var add = this.previousSibling.innerHTML;
            add = add.slice(3)
            price += parseFloat(add)
                if (order.selected_orderline.product.pos_variants){
                    variant.push({  'extra_price': add,
                        'type': $(this).data('type'),
                    })
                };
            })
            selected_orderline.price_manually_set = true;
            selected_orderline.price += price
            selected_orderline.trigger('change', selected_orderline);
            this.trigger('close-popup')
        }

        imageUrl() {
                    return `/web/image?model=product.product&field=image_1920&id=${this.props.product_tmpl_id}&unique=1`;
                    }


        async _clickProduct(event) {
        }
    }
    //products popup template
    ProductsPopup.template = 'ProductsPopUp';
    ProductsPopup.defaultProps = {};

    Registries.Component.add(ProductsPopup);
    return ProductsPopup;
});
