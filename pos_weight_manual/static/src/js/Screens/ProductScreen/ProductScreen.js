/** @odoo-module **/

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const PosWeightProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
             if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            const product = event.detail;
            const options = await this._getAddProductOptions(product);
            if(this.env.pos.res_button.length){
                if (this.env.pos.res_button[this.env.pos.res_button.length - 1].is_allow_manual_weight === true) {
                    // Show the ScaleScreen to weigh the product.
                     const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
                            product,
                     });
                     if (confirmed) {
                           options['quantity'] = payload.weight
                           await this._addProduct(product, options);
                     } else {
                            // do not add the product;
                        return;
                     }
                } else{
                // add product if allow manual button is not enabled in the settings.
                await this._addProduct(product, options);
                }
            }else{
            // add product if allow manual button is not enabled in the settings.
            await this._addProduct(product, options);
            }
            // Do not add product if options is undefined.
            if (!options) return;
            // Add the product after having the extra information.
            }
        };
    Registries.Component.extend(ProductScreen, PosWeightProductScreen);
    return ProductScreen;
