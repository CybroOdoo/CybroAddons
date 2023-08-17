odoo.define('pos_product_creation.product_create_button', function(require) {
   'use strict';
   const PosComponent = require('point_of_sale.PosComponent');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');
   const ajax = require('web.ajax');

   class ProductCreateButton extends PosComponent {
        setup() {
            super.setup();
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
                if (image){
                    if(image.type == "image/jpeg"){
                        await reader.readAsDataURL(image);
                    } else {
//                        return self.showPopup('ErrorPopup', {
//                          title: _('Choose Image In JPEG Format'),
//                        });
                        return self.showPopup('ErrorPopup', {
                            title: self.env._t('Filed Error'),
                            body: self.env._t('Choose Image In JPEG Format.'),
                         });
                    }
                } else {
                    return self.showPopup('ErrorPopup', {
                        title: self.env._t('Empty Filed'),
                        body: self.env._t('All Fields Are Required.'),
                    });
                }
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
                    let datas = {
                        'category': product_category,
                        'image': image,
                        'name': product_name,
                        'price': product_price,
                        'product_reference': product_reference,
                        'unit_measure': unit_measure,
                        'product_categories': product_categories,
                        'barcode': barcode,
                    }
                    for (const [key, value] of Object.entries(datas)){
                        if (value === null || value === undefined){
                            var errorFound = 1;
                        } else {
                            let errorFound = 0;
                        }
                    }
                    if (errorFound == 1){
                        return self.showPopup('ErrorPopup', {
                            title: self.env._t('Empty Filed'),
                            body: self.env._t('All Fields Are Required.'),
                        });
                    } else {
                        ajax.jsonRpc('/create_product', 'call', datas)
                    }
                }

           }
        }
    }
    ProductCreateButton.template = 'ProductCreateButton';
    ProductScreen.addControlButton({
        component: ProductCreateButton,
        condition: function() {
            return this;
        },
        position: ['before', 'SetPricelistButton'],
    });

    Registries.Component.add(ProductCreateButton);
    return ProductCreateButton;
});
