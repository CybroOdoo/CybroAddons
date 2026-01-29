/** @odoo-module **/

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const PosWeightProductScreen = (ProductScreen) =>
        class extends ProductScreen {
        get currentOrder() {
            return this.env.pos.get_order();
        }
            async _clickProduct(event) {
             if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            const product = event.detail;
            const options = await this._getAddProductOptions(product);
            if(this.env.pos.is_allow_manual_weight.length){
                if (this.env.pos.is_allow_manual_weight[this.env.pos.is_allow_manual_weight.length - 1].is_allow_manual_weight === true) {
                    // Show the ScaleScreen to weigh the product.
                     const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
                            product,
                     });
                     if (confirmed) {
                           options['quantity'] = payload.weight
                           await this.currentOrder.add_product(product, options);
                     } else {
                            // do not add the product;
                        return;
                     }
                } else{
                // add product if allow manual button is not enabled in the settings.
                await this.currentOrder.add_product(product, options);
                }
            }else{
            // add product if allow manual button is not enabled in the settings.
            await this.currentOrder.add_product(product, options);
            }
            // Do not add product if options is undefined.
            if (!options) return;
            // Add the product after having the extra information.
            }
        };
    Registries.Component.extend(ProductScreen, PosWeightProductScreen);
    return ProductScreen;
