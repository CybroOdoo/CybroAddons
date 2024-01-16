odoo.define('laundry_management_pos.product_create_button', function(require) {
    'use strict';

const PosComponent = require('point_of_sale.PosComponent');
const ProductScreen = require('point_of_sale.ProductScreen');
const { useListener } = require('web.custom_hooks');
const Registries = require('point_of_sale.Registries');
const ajax = require('web.ajax');

// Extending the PosComponent that used to create a button in the POS View
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
        console.log(payload, 'payload')
            var product_category = payload[0];
            var product_name = payload[1];
            var product_reference = payload[2];
            var product_price = payload[3];
            var unit_measure = payload[4];
            var product_categories = payload[5];
            var pos_categories = payload[6];
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
                'pos_categories': pos_categories
            }).then(function(response) {});
        }
    }
}
// Create a new Button that used to Display the Product Information
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