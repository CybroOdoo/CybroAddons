/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ScaleScreen } from "@pos_weight_manual/js/scale_screen";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, merge = true) {
        merge = false;
        let order = this.getOrder();
        order.assertEditable();

        if (!order) {
            order = this.addNewOrder();
        }

        const options = {
            ...opts,
        };

        if ("price_unit" in vals) {
            merge = false;
        }
        const product = vals.product_tmpl_id;
        const productPrice = product.list_price || product.price || 0;

        const values = {
            price_type: "price_unit" in vals ? "manual" : "original",
            price_extra: 0,
            price_unit: productPrice,
            order_id: this.getOrder(),
            qty: 1,
            tax_ids: product.taxes_id.map((tax) => ["link", tax]),
            ...vals,
        };

        if (!('price_unit' in vals) && productPrice > 0) {
            values.price_unit = productPrice;
        }
        if (this.env.services.pos.config.is_allow_manual_weight) {
            if (values.product_tmpl_id.isScaleAvailable) {
                this.isScaleScreenVisible = true;
                this.scaleData = {
                    productName: values.product_tmpl_id?.display_name,
                    uomName: values.product_tmpl_id.uom_id?.name,
                    uomRounding: values.product_tmpl_id.uom_id?.rounding,
                    productPrice: productPrice,
                };
                const weight = await makeAwaitable(
                    this.env.services.dialog,
                    ScaleScreen,
                    this.scaleData
                );
                if (!weight) {
                    return;
                }
                values.qty = weight;
                this.isScaleScreenVisible = false;
                this.scaleWeight = 0;
                this.scaleTare = 0;
                this.totalPriceOnScale = 0;
            } else {
                await values.product_id._onScaleNotAvailable();
            }
        }

        return super.addLineToCurrentOrder(values, options, merge);
    },

    async addLineToOrder(vals, order, opts = {}, configure = true) {
        let merge = true;
        order.assertEditable();

        const options = {
            ...opts,
        };

        if ("price_unit" in vals) {
            merge = false;
        }

        if (typeof vals.product_tmpl_id == "number") {
            vals.product_tmpl_id = this.data.models["product.template"].get(vals.product_tmpl_id);
        }
        const productTemplate = vals.product_tmpl_id;
        const values = {
            price_type: "price_unit" in vals ? "manual" : "original",
            price_extra: 0,
            price_unit: 0,
            order_id: this.getOrder(),
            qty: this.getOrder().preset_id?.is_return ? -1 : 1,
            tax_ids: productTemplate.taxes_id.map((tax) => ["link", tax]),
            product_id: productTemplate.product_variant_ids[0],
            ...vals,
        };

        // Handle refund constraints
        if (order.isSaleDisallowed(values, options)) {
            this.dialog.add(AlertDialog, {
                title: _t("Oops.."),
                body: _t("Ensure you validate the refund before taking another order."),
            });
            return;
        }

        // In case of configurable product a popup will be shown to the user
        // We assign the payload to the current values object.
        // ---
        // This actions cannot be handled inside pos_order.js or pos_order_line.js
        if (productTemplate.isConfigurable() && configure) {
            const payload =
                vals?.payload && Object.keys(vals?.payload).length
                    ? vals.payload
                    : await this.openConfigurator(productTemplate, opts);

            if (payload) {
                // Find candidate based on instantly created variants.
                const attributeValues = this.models["product.template.attribute.value"]
                    .readMany(payload.attribute_value_ids)
                    .filter((value) => value.attribute_id.create_variant !== "no_variant")
                    .map((value) => value.id);

                let candidate = productTemplate.product_variant_ids.find((variant) => {
                    const attributeIds = variant.product_template_attribute_value_ids.map(
                        (value) => value.id
                    );
                    return (
                        attributeValues.every((id) => attributeIds.includes(id)) &&
                        attributeValues.length
                    );
                });

                const isDynamic = productTemplate.attribute_line_ids.some(
                    (line) => line.attribute_id.create_variant === "dynamic"
                );

                if (!candidate && isDynamic) {
                    // Need to create the new product.
                    const result = await this.data.callRelated(
                        "product.template",
                        "create_product_variant_from_pos",
                        [productTemplate.id, payload.attribute_value_ids, this.config.id]
                    );
                    candidate = result["product.product"][0];
                }

                Object.assign(values, {
                    attribute_value_ids: payload.attribute_value_ids.map((id) => [
                        "link",
                        this.models["product.template.attribute.value"].get(id),
                    ]),
                    custom_attribute_value_ids: Object.entries(payload.attribute_custom_values).map(
                        ([id, cus]) => [
                            "create",
                            {
                                custom_product_template_attribute_value_id:
                                    this.models["product.template.attribute.value"].get(id),
                                custom_value: cus,
                            },
                        ]
                    ),
                    price_extra: values.price_extra + payload.price_extra,
                    qty: payload.qty || values.qty,
                    product_id: candidate || productTemplate.product_variant_ids[0],
                });
            } else {
                return;
            }
        } else if (values.product_id.product_template_variant_value_ids.length > 0) {
            // Verify price extra of variant products
            const priceExtra = values.product_id.product_template_variant_value_ids
                .filter((attr) => attr.attribute_id.create_variant !== "always")
                .reduce((acc, attr) => acc + attr.price_extra, 0);

            values.price_extra += priceExtra;
            if (!values.attribute_value_ids) {
                values.attribute_value_ids = [];
            }
            values.attribute_value_ids = values.attribute_value_ids.concat(
                values.product_id.product_template_variant_value_ids.map((attr) => ["link", attr])
            );
        }

        // In case of clicking a combo product a popup will be shown to the user
        // It will return the combo prices and the selected products
        // ---
        // This actions cannot be handled inside pos_order.js or pos_order_line.js
        if (values.product_tmpl_id.isCombo() && configure) {
            const payload =
                vals?.payload && Object.keys(vals?.payload).length
                    ? vals.payload
                    : await makeAwaitable(this.dialog, ComboConfiguratorPopup, {
                          productTemplate: values.product_tmpl_id,
                      });

            if (!payload) {
                return;
            }

            // Product template of combo should not have more than 1 variant.
            const [childLineConf, comboExtraLines] = payload;
            const comboPrices = computeComboItems(
                values.product_tmpl_id.product_variant_ids[0],
                childLineConf,
                order.pricelist_id,
                this.data.models["decimal.precision"].getAll(),
                this.data.models["product.template.attribute.value"].getAllBy("id"),
                comboExtraLines,
                this.currency
            );

            values.combo_line_ids = comboPrices.map((comboItem) => [
                "create",
                {
                    product_id: comboItem.combo_item_id.product_id,
                    tax_ids: comboItem.combo_item_id.product_id.taxes_id.map((tax) => [
                        "link",
                        tax,
                    ]),
                    combo_item_id: comboItem.combo_item_id,
                    price_unit: comboItem.price_unit,
                    price_type: "automatic",
                    order_id: order,
                    qty: comboItem.qty,
                    attribute_value_ids: comboItem.attribute_value_ids?.map((attr) => [
                        "link",
                        attr,
                    ]),
                    custom_attribute_value_ids: Object.entries(
                        comboItem.attribute_custom_values
                    ).map(([id, cus]) => [
                        "create",
                        {
                            custom_product_template_attribute_value_id:
                                this.data.models["product.template.attribute.value"].get(id),
                            custom_value: cus,
                        },
                    ]),
                },
            ]);
        }

        // In the case of a product with tracking enabled, we need to ask the user for the lot/serial number.
        // It will return an instance of pos.pack.operation.lot
        // ---
        // This actions cannot be handled inside pos_order.js or pos_order_line.js
        const code = opts.code;
        let pack_lot_ids = {};
        if (values.product_tmpl_id.isTracked() && (configure || code)) {
            const packLotLinesToEdit =
                (!values.product_tmpl_id.isAllowOnlyOneLot() &&
                    this.getOrder()
                        .getOrderlines()
                        .filter((line) => !line.getDiscount())
                        .find((line) => line.product_id.id === values.product_id.id)
                        ?.getPackLotLinesToEdit()) ||
                [];

            // if the lot information exists in the barcode, we don't need to ask it from the user.
            if (code && code.type === "lot") {
                // consider the old and new packlot lines
                const modifiedPackLotLines = Object.fromEntries(
                    packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                );
                const newPackLotLines = [{ lot_name: code.code }];
                pack_lot_ids = { modifiedPackLotLines, newPackLotLines };
            } else {
                pack_lot_ids = await this.editLots(values.product_id, packLotLinesToEdit);
            }

            if (!pack_lot_ids) {
                return;
            } else {
                const packLotLine = pack_lot_ids.newPackLotLines;
                values.pack_lot_ids = packLotLine.map((lot) => ["create", lot]);
            }
        }

        // In case of clicking a product with tracking weight enabled a popup will be shown to the user
        // It will return the weight of the product as quantity
        // ---
        // This actions cannot be handled inside pos_order.js or pos_order_line.js
        if (values.product_tmpl_id.to_weight && this.config.iface_electronic_scale && configure) {
            if (values.product_tmpl_id.isScaleAvailable) {
            // starting show scale screen
                this.isScaleScreenVisible = true;
                this.scaleData = {
                    productName: values.product_id?.display_name,
                    uomName: values.product_id.uom_id?.name,
                    uomRounding: values.product_id.uom_id?.rounding,
                    productPrice: this.getProductPrice(values.product_id),
                };
                const weight = await makeAwaitable(
                    this.env.services.dialog,
                    ScaleScreen,
                    this.scaleData
                );
                if (!weight) {
                    return;
                }
                values.qty = weight;
                this.isScaleScreenVisible = false;
                this.scaleWeight = 0;
                this.scaleTare = 0;
                this.totalPriceOnScale = 0;
            // ending show scale screen
            } else {
                await values.product_tmpl_id._onScaleNotAvailable();
            }
        }

        // Handle price unit
        if (!values.product_tmpl_id.isCombo() && vals.price_unit === undefined) {
            values.price_unit = values.product_id.getPrice(
                order.pricelist_id,
                values.qty,
                values.price_extra,
                false,
                values.product_id
            );
        }

        const line = this.data.models["pos.order.line"].create({ ...values, order_id: order });
        line.setOptions(options);
        this.selectOrderLine(order, line);
        if (configure) {
            this.numberBuffer.reset();
        }
        const selectedOrderline = order.getSelectedOrderline();
        if (options.draftPackLotLines && configure) {
            selectedOrderline.setPackLotLines({
                ...options.draftPackLotLines,
                setQuantity: options.quantity === undefined,
            });
        }

        let to_merge_orderline;
        for (const curLine of order.lines) {
            if (curLine.id !== line.id) {
                if (curLine.canBeMergedWith(line) && merge !== false) {
                    to_merge_orderline = curLine;
                }
            }
        }

        if (to_merge_orderline) {
            to_merge_orderline.merge(line);
            line.delete();
            this.selectOrderLine(order, to_merge_orderline);
        } else if (!selectedOrderline) {
            this.selectOrderLine(order, order.getLastOrderline());
        }

        if (configure) {
            this.numberBuffer.reset();
        }

        if (values.product_id.tracking === "serial") {
            this.selectedOrder.getSelectedOrderline().setPackLotLines({
                modifiedPackLotLines: pack_lot_ids.modifiedPackLotLines ?? [],
                newPackLotLines: pack_lot_ids.newPackLotLines ?? [],
                setQuantity: true,
            });
        }

        if (configure) {
            this.numberBuffer.reset();
        }

        this.hasJustAddedProduct = true;
        clearTimeout(this.productReminderTimeout);
        this.productReminderTimeout = setTimeout(() => {
            this.hasJustAddedProduct = false;
        }, 3000);

        return order.getSelectedOrderline();
    }
});
