odoo.define('pos_pro_cross_selling.CrossProducts', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const {
        useListener
    } = require("@web/core/utils/hooks");
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductItem = require('point_of_sale.ProductItem');
    var models = require('point_of_sale.models');

    class CrossProducts extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-product', this._onClickOrder);
        }

        confirm() {
            // Adding  Products into the order line
            super.confirm();
            var product = this.props.products
            for (var i = 0; i < product.length; i++) {
                if (product[i].selected == true) {
                    this.env.pos.get_order().add_product(this.env.pos.db.product_by_id[product[i].id]);
                }
            }
        }

        _onClickOrder(event, product) {
            // Selecting or deselecting cross-sell products
            const products = this.props.products;
            const id = product.id;
            const $ribbonElements = $(".ribbon-3");

            products.forEach(prod => {
                if (prod.id === id) {
                    prod.selected = !prod.selected; // Toggle selected state
                    $ribbonElements.each(function () {
                        const $element = $(this);
                        if ($element.data('id') === id) {
                            $element.css('display', prod.selected ? 'block' : 'none');
                        }
                    });
                }
            });
        }
    }
    //products popup template
    CrossProducts.template = 'CrossProducts';
    CrossProducts.defaultProps = {
        cancelKey: false
    };
    Registries.Component.add(CrossProducts);
    return CrossProducts;
});