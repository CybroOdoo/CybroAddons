odoo.define("pos_auto_lot_selection.product", function (require) {
    "use strict";
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const NumberBuffer = require("point_of_sale.NumberBuffer");
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
                    const orderline = this.currentOrder
                        .get_orderlines()
                        .find(line => line.product.id === product.id && !line.get_discount());
                    if (isAllowOnlyOneLot) {
                        packLotLinesToEdit = [];
                    } else {
                        packLotLinesToEdit = orderline ? orderline.getPackLotLinesToEdit() : [];
                    }
                    // if the lot information exists in the barcode, we don't need to ask it from the user.
                    if (base_code && base_code.type === 'lot') {
                        // consider the old and new packlot lines
                        const modifiedPackLotLines = Object.fromEntries(
                            packLotLinesToEdit.filter(item => item.id).map(item => [item.id, item.text])
                        );
                        const newPackLotLines = [
                            { lot_name: base_code.code },
                        ];
                        draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                    } else {
                        let quantity = 1;
                        if (weight) {
                            quantity = weight;
                        } else if (NumberBuffer.get()) {
                            quantity = NumberBuffer.getFloat();
                        }
                        if (quantity <= 0) {
                            quantity = 1;
                        }

                        if (!this.currentOrder) {
                            this.env.pos.add_new_order();
                        }

                        let fetched_assigned_lots = [];
                        if (this.currentOrder) {
                            this.currentOrder.get_orderlines().forEach(line => {
                                if (line.product.id === product.id) {
                                    const linesToEdit = line.getPackLotLinesToEdit();
                                    if (linesToEdit && Array.isArray(linesToEdit)) {
                                        linesToEdit.forEach(item => {
                                            if (item.text) {
                                                fetched_assigned_lots.push(item.text);
                                            }
                                        });
                                    }
                                }
                            });
                        }

                        try {
                            const result = await this.rpc({
                                model: "stock.lot",
                                method: "get_available_lots_for_pos",
                                args: [product.id, quantity, fetched_assigned_lots],
                            });

                            if (result) {
                                const modifiedPackLotLines = Object.fromEntries(
                                    packLotLinesToEdit.filter(item => item.id)
                                        .map(item => [item.id, item.text])
                                );
                                const newPackLotLines = result.map(item => ({ lot_name: item }));
                                draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                            } else {
                                await this.showPopup('ErrorPopup', {
                                    title: this.env._t("Serial/Lot Numbers are missing"),
                                    body: this.env._t("You are trying to sell products with serial/lot numbers, but some of them are not set. Please set the serial/lot numbers for this product."),
                                });
                                return;
                            }
                        } catch (error) {
                            await this.showPopup('ErrorPopup', {
                                title: this.env._t("RPC Error"),
                                body: this.env._t("An error occurred while fetching available lots."),
                            });
                            return;
                        }
                    }
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
