/** @odoo-module **/

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { useBarcodeReader } = require('point_of_sale.custom_hooks');
    class FindProductScreen extends PosComponent {
        setup(){
            super.setup();
              useBarcodeReader({
            product: this._barcodeProductAction
        });
        }
        //Barcode scan detect function
        async _barcodeProductAction(code) {
        var self = this;
        rpc.query({
            model: 'product.template',
            method: 'product_detail_search',
            args: [[], code.base_code],
            }).then(function(result) {
            if (result==false) {
                self.showScreen('ProductDetails', {
                'product_details' : false,
                });
            }
            else {
                self.product_details = result
                self.showScreen('ProductDetails', {
                'product_details' : self.product_details,
                });
            }
            });
        }
        //Returning the Product Screen
        back() {
            this.showScreen('ProductScreen');
        }
    };
  FindProductScreen.template = 'FindProductScreen';
  Registries.Component.add(FindProductScreen);
  return FindProductScreen;
