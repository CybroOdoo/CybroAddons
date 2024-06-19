odoo.define("all_in_one_pos_kit.auto_lot", function (require) {
    "use strict";
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    var rpc = require('web.rpc');
    /**
     * Extends the ProductScreen component to add automatic lot handling functionality.
     * This component overrides the "_getAddProductOptions" method to include automatic lot handling for products
     * with tracking enabled. It retrieves available lots for the product and allows the user to select the lot
     * during the product addition process.
     */
    const PosLotSaleProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _getAddProductOptions(product, base_code) {//Override the `_getAddProductOptions` method to include lot information retrieval and handling.
            let price_extra = 0.0;
            let draftPackLotLines, weight, description, packLotLinesToEdit;
            if (_.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
                let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
                                  .filter((attr) => attr !== undefined);
                let { confirmed, payload } = await this.showPopup('ProductConfiguratorPopup', {
                    product: product,
                    attributes: attributes,
                });
                if (confirmed) {
                    description = payload.selected_attributes.join(', ');
                    price_extra += payload.price_extra;
                } else {
                    return;
                }
            }
            // Gather lot information if required.
            if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
                if (isAllowOnlyOneLot) {
                    packLotLinesToEdit = [];
                } else {
                    const orderline = this.currentOrder
                        .get_orderlines()
                        .filter(line => !line.get_discount())
                        .find(line => line.product.id === product.id);
                    if (orderline) {
                        packLotLinesToEdit = orderline.getPackLotLinesToEdit();
                    } else {
                        packLotLinesToEdit = [];
                    }
                }
            await rpc.query({//RPC to get value from the model stock_lot
                model: "stock.lot",
                method: "get_available_lots_for_pos",
                args: [product.id],
                }).then(function (result) {
                const modifiedPackLotLines =  result[0];
                    const newPackLotLines = result.map(item => ({ lot_name: result[0] }));
                    draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                });
            }
            // Take the weight if necessary.
            if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
                // Show the ScaleScreen to weigh the product.
                if (this.isScaleAvailable) {
                    const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
                        product,
                    });
                    if (confirmed) {
                        weight = payload.weight;
                    } else {
                        // do not add the product;
                        return;
                    }
                } else {
                    await this._onScaleNotAvailable();
                }
            }
            if (base_code && this.env.pos.db.product_packaging_by_barcode[base_code.code]) {
                weight = this.env.pos.db.product_packaging_by_barcode[base_code.code].qty;
            }
            return { draftPackLotLines, quantity: weight, description, price_extra };
        }
        };
    Registries.Component.extend(ProductScreen, PosLotSaleProductScreen);
    return ProductScreen;
});
