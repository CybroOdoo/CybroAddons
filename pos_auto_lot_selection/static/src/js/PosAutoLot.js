odoo.define('pos_auto_lot_selection.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');

    const PosAutoLotSelection = (ProductScreen) =>
        class extends ProductScreen {
                constructor() {
                    super(...arguments);
                }
                async _getAddProductOptions(product, code) {
                    let price_extra = 0.0;
                    let draftPackLotLines, weight, description, packLotLinesToEdit;
                    let productConfiguratorPayload;
                    if (this.env.pos.config.product_configurator && _.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
                        let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
                                          .filter((attr) => attr !== undefined);
                        let { confirmed, payload } = await this.showPopup('ProductConfiguratorPopup', {
                            product: product,
                            attributes: attributes,
                        });
                        productConfiguratorPayload = payload;
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
                        // if the lot information exists in the barcode, we don't need to ask it from the user.
                        if (code && code.type === 'lot') {
                            // consider the old and new packlot lines
                            const modifiedPackLotLines = Object.fromEntries(
                                packLotLinesToEdit.filter(item => item.id).map(item => [item.id, item.text])
                            );
                            const newPackLotLines = [
                                { lot_name: code.code },
                            ];
                            draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                        } else {
                            const result = await this.rpc({
                                model: 'stock.production.lot',
                                method: 'get_available_lots_for_pos',
                                args: [[product.id]],
                            });
                            if(!result[0]){
                                const { confirmed, payload } = await this.showPopup('EditListPopup', {
                                    title: this.env._t('Lot/Serial Number(s) Required'),
                                    isSingleItem: isAllowOnlyOneLot,
                                    array: packLotLinesToEdit,
                                });
                                if (confirmed) {
                                     // Segregate the old and new packlot lines
                                    const modifiedPackLotLines = Object.fromEntries(
                                        payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                                    );
                                    const newPackLotLines = payload.newArray.filter(item => !item.id).map(item => ({ lot_name: item.text }));

                                    draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                                } else {
                                    // We don't proceed on adding product.
                                    return;
                                }
                            }
                            else{
                                const modifiedPackLotLines =  result[0];
                                const newPackLotLines = result.map(item => ({ lot_name: result[0] }));
                                draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
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

                    if (code && this.env.pos.db.product_packaging_by_barcode[code.code]) {
                        weight = this.env.pos.db.product_packaging_by_barcode[code.code].qty;
                    }
                return { draftPackLotLines, quantity: weight, description, price_extra, productConfiguratorPayload };
        }
        };

    Registries.Component.extend(ProductScreen, PosAutoLotSelection);

    return ProductScreen;
});
