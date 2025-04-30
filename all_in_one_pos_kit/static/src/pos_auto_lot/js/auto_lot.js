odoo.define("all_in_one_pos_kit.auto_lot", function (require) {
    "use strict";
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    var rpc = require('web.rpc');
//Extending ProductScreen
    const PosLotSaleProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _getAddProductOptions(product, code) {
            let price_extra = 0.0;
            let draftPackLotLines, weight, description, packLotLinesToEdit;
            let productConfiguratorPayload;
            if (this.env.pos.config.product_configurator && _.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
                let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
                                  .filter((attr) => attr !== undefined);
                    if (attributes.length > 0) {
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
                }
                // Gather lot information if required.
                if (['serial', 'lot'].includes(product.tracking) &&
                    (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
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
                    try {
                        const result = await rpc.query({
                            model: "stock.production.lot",
                            method: "get_available_lots_for_pos",
                            args: [product.id],
                        });

                        const modifiedPackLotLines = result[0];
                        const newPackLotLines = result.map(item => ({ lot_name: result[0] }));
                        draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                    } catch (error) {
                        console.error('Error fetching lots:', error);
                        return;
                    }
                }
                // Take the weight if necessary.
                if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
                    if (this.isScaleAvailable) {
                        const { confirmed, payload } = await this.showTempScreen('ScaleScreen', { product });
                        if (confirmed) {
                            weight = payload.weight;
                        } else {
                            return;
                        }
                    } else {
                        await this._onScaleNotAvailable();
                    }
                }
                if (code && this.env.pos.db.product_packaging_by_barcode[code.code]) {
                    weight = this.env.pos.db.product_packaging_by_barcode[code.code].qty;
                }
                return { draftPackLotLines, quantity: weight, description, price_extra };
            }
        };

    Registries.Component.extend(ProductScreen, PosLotSaleProductScreen);
    return ProductScreen;
});
