odoo.define('owl_tutorials.product_create_button', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {
        useListener
    } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
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
                var product_image;
                var image = $('#product-image')[0].files[0]
                var reader = new FileReader();
                await reader.readAsDataURL(image);
                reader.onload = function(){
                    product_image = reader.result
                    var image = product_image.slice(23);
                    var product_category = payload[0];
                    var product_name = payload[1];
                    var product_reference = payload[3];
                    var product_price = payload[4];
                    var unit_measure = payload[5];
                    var product_categories = payload[6];
                    var barcode = payload[7];
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
                        'image': image,
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