odoo.define('owl_tutorials.product_create_button', function(require) {
    'use strict';
   const { Gui } = require('point_of_sale.Gui');
   const PosComponent = require('point_of_sale.PosComponent');
   const { posbus } = require('point_of_sale.utils');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require('web.custom_hooks');
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   const ajax = require('web.ajax');

    class ProductCreateButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            const {
                confirmed,
                payload
            } = await this.showPopup('ProductCreatePopup', {
                title: this.env._t('POS Product Creation'),
                body: this.env._t('You can Create The product.'),
            });
            if (confirmed) {
                var product_category = payload[0];
                var product_name = payload[1];
                var product_reference = payload[2];
                var product_price = payload[3];
                var unit_measure = payload[4];
                var product_categories = payload[5];
                var barcode = payload[6];
                if (!product_name){
                    return this.showPopup('ErrorPopup', {
                      title: _('A Unit Of Measure Is Required'),
                    });
                }
                if (!unit_measure){
                    return this.showPopup('ErrorPopup', {
                      title: _('A Unit Of Measure Is Required'),
                    });
                }
                ajax.jsonRpc('/create_product', 'call', {
                    'category': product_category,
                    'name': product_name,
                    'price': product_price,
                    'product_reference': product_reference,
                    'unit_measure': unit_measure,
                    'product_categories': product_categories,
                    'barcode': barcode,
                }).then(function(response) {});
           }
        }
    }
    ProductCreateButton.template = 'ProductCreateButton';
    ProductScreen.addControlButton({
        component: ProductCreateButton,
        condition: function() {
            return true;
        },
        position: ['before', 'SetPricelistButton'],
    });

    Registries.Component.add(ProductCreateButton);

    return ProductCreateButton;
});