odoo.define('laundry_management_pos.product_create_button', function(require) {
    'use strict';

const PosComponent = require('point_of_sale.PosComponent');
const ProductScreen = require('point_of_sale.ProductScreen');
const { useListener } = require("@web/core/utils/hooks");
const Registries = require('point_of_sale.Registries');
const ajax = require('web.ajax');
const { Gui } = require('point_of_sale.Gui');

// Extending the PosComponent that used to create a button in the POS View
class ProductCreateButton extends PosComponent {
     async setup() {
            super.setup();
            await this.loadProductCategory();
     }
     async loadProductCategory() {
            // Method for loading product categories
            const product_categories = await this.rpc({
                model: 'product.category',
                method: 'search_read',
                fields: ['name', 'complete_name'],
            });
            this.env.pos.product_categories = product_categories;
        }
     async _onClickCreateProduct(e) {
     //Method for opening the popup
        var self = this;
         const core = require('web.core');
            const _t = core._t;
            const { confirmed, payload } = await Gui.showPopup("ProductCreatePopup", {
                title: _t("POS Product Creation"),
                confirmText: _t("Exit"),
            });
        if (confirmed) {
            var product_category = payload[0];
            var product_name = payload[1];
            var product_reference = payload[2];
            var product_price = payload[3];
            var unit_measure = payload[4];
            var product_categories = payload[5];
            var pos_categories = payload[6];
            if (!product_name){
                return this.showPopup('ErrorPopup', {
                  title: _('Product Name is Required'),
                });
            }
            if (!unit_measure){
                return this.showPopup('ErrorPopup', {
                  title: _('A Unit Of Measure is Required'),
                });
            }
            if (!product_categories){
                return this.showPopup('ErrorPopup', {
                  title: _('Product Category is Required'),
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
