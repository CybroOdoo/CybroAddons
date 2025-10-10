/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Product } from "@point_of_sale/app/store/models";
import { _t } from "@web/core/l10n/translation";
import { ComboConfiguratorPopup } from "@point_of_sale/app/store/combo_configurator_popup/combo_configurator_popup";

patch(Product.prototype, {
    async getAddProductOptions(code) {
        let price_extra = 0.0;
        let draftPackLotLines, packLotLinesToEdit, attribute_value_ids;
        let quantity = 1;
        let comboLines = [];
        let attribute_custom_values = {};

        if (code && this.pos.db.product_packaging_by_barcode[code.code]) {
            quantity = this.pos.db.product_packaging_by_barcode[code.code].qty;
        }

        if (this.isConfigurable()) {
            const { confirmed, payload } = await this.openConfigurator({ initQuantity: quantity });
            if (confirmed) {
                attribute_value_ids = payload.attribute_value_ids;
                attribute_custom_values = payload.attribute_custom_values;
                price_extra += payload.price_extra;
                quantity = payload.quantity;
            } else {
                return;
            }
        }

        if (this.combo_ids.length) {
            const { confirmed, payload } = await this.env.services.popup.add(
                ComboConfiguratorPopup,
                { product: this, keepBehind: true }
            );
            if (!confirmed) {
                return;
            }
            comboLines = payload;
        }

        // Gather lot information if required.
        if (this.isTracked()) {
            packLotLinesToEdit =
                (!this.isAllowOnlyOneLot() &&
                    this.pos.selectedOrder
                        .get_orderlines()
                        .filter((line) => !line.get_discount())
                        .find((line) => line.product.id === this.id)
                        ?.getPackLotLinesToEdit()) ||
                [];

            // If lot from barcode
            if (code && code.type === "lot") {
                const modifiedPackLotLines = Object.fromEntries(
                    packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                );
                const newPackLotLines = [{ lot_name: code.code }];
                draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
            } else {
                // Check location stock and get lots
                try {
                    const result = await this.env.services.orm.call(
                        "stock.lot",
                        "get_available_lots_for_pos",
                        [],
                        {
                            product_id: this.id,
                            pos_config_id: this.pos.config.id
                        }
                    );

                    console.log("=========================================");
                    console.log("Product:", this.display_name);
                    console.log("Has Positive Stock:", result.has_positive_stock);
                    console.log("Total Qty in Location:", result.total_quantity);
                    console.log("Available Lots:", result.lots);
                    console.log("=========================================");

                    // DECISION: Auto-assign if positive stock, manual if not
                    if (result.has_positive_stock === true) {
                        console.log("→ POSITIVE STOCK - AUTO ASSIGNING LOT");

                        if (result.lots && result.lots.length > 0) {
                            // Calculate already used quantities
                            const usedLotQty = {};
                            const orderLines = this.pos.selectedOrder.get_orderlines();

                            for (const line of orderLines) {
                                if (line.product.id === this.id && line.pack_lot_lines) {
                                    for (const lotLine of line.pack_lot_lines) {
                                        if (lotLine.lot_name) {
                                            usedLotQty[lotLine.lot_name] =
                                                (usedLotQty[lotLine.lot_name] || 0) + line.quantity;
                                        }
                                    }
                                }
                            }

                            console.log("Used quantities:", usedLotQty);

                            // Find first lot with remaining quantity
                            let selectedLot = null;
                            for (const lot of result.lots) {
                                const used = usedLotQty[lot.lot_name] || 0;
                                const remaining = lot.available_qty - used;
                                console.log(`Lot ${lot.lot_name}: available=${lot.available_qty}, used=${used}, remaining=${remaining}`);

                                if (remaining > 0) {
                                    selectedLot = lot;
                                    break;
                                }
                            }

                            if (selectedLot) {
                                console.log("✓ Selected lot:", selectedLot.lot_name);
                                draftPackLotLines = {
                                    modifiedPackLotLines: {},
                                    newPackLotLines: [{ lot_name: selectedLot.lot_name }]
                                };
                            } else {
                                console.log("✗ All lots exhausted in order");
                                await this.env.services.popup.add('ErrorPopup', {
                                    title: _t('No Available Stock'),
                                    body: _t('All available lots have been added to the order.'),
                                });
                                return;
                            }
                        } else {
                            console.log("✗ No lots found but stock is positive");
                            // Continue without assigning lot - will be handled by standard flow
                            draftPackLotLines = {
                                modifiedPackLotLines: Object.fromEntries(
                                    packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                                ),
                                newPackLotLines: []
                            };
                        }
                    } else {
                        console.log("→ NO POSITIVE STOCK - ADDING PRODUCT WITHOUT LOT");
                        console.log("User can add lot manually from orderline");
                        // Add product without lot - user can edit from orderline
                        draftPackLotLines = {
                            modifiedPackLotLines: Object.fromEntries(
                                packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                            ),
                            newPackLotLines: []
                        };
                    }
                } catch (error) {
                    console.error("ERROR:", error);
                    // Fallback - add without lot
                    draftPackLotLines = {
                        modifiedPackLotLines: Object.fromEntries(
                            packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                        ),
                        newPackLotLines: []
                    };
                }
            }

            if (!draftPackLotLines) {
                return;
            }
        }

        // Take the weight if necessary.
        if (this.to_weight && this.pos.config.iface_electronic_scale) {
            if (this.isScaleAvailable) {
                const { confirmed, payload } = await this.env.services.pos.showTempScreen(
                    "ScaleScreen",
                    { product: this }
                );
                if (confirmed) {
                    quantity = payload.weight;
                } else {
                    return;
                }
            } else {
                await this._onScaleNotAvailable();
            }
        }

        return {
            draftPackLotLines,
            quantity,
            attribute_custom_values,
            price_extra,
            comboLines,
            attribute_value_ids,
        };
    }
});
