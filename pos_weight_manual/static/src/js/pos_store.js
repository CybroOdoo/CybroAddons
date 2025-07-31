/** @odoo-module **/
import { Component } from "@odoo/owl";
import { ScaleScreen } from "@pos_weight_manual/js/scale_screen";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, merge = true) {
        merge = false;
        let order = this.get_order();
        order.assert_editable();

        if (!order) {
            order = this.add_new_order();
        }

        const options = {
            ...opts,
        };

        if ("price_unit" in vals) {
            merge = false;
        }

        const product = vals.product_id;
        const productPrice = product.lst_price || product.price || 0;

        const values = {
            price_type: "price_unit" in vals ? "manual" : "original",
            price_extra: 0,
            price_unit: productPrice,
            order_id: this.get_order(),
            qty: 1,
            tax_ids: product.taxes_id.map((tax) => ["link", tax]),
            ...vals,
        };

        if (!('price_unit' in vals) && productPrice > 0) {
            values.price_unit = productPrice;
        }

        if (this.env.services.pos.config.is_allow_manual_weight) {
            if (values.product_id.isScaleAvailable) {
                this.isScaleScreenVisible = true;
                this.scaleData = {
                    productName: values.product_id?.display_name,
                    uomName: values.product_id.uom_id?.name,
                    uomRounding: values.product_id.uom_id?.rounding,
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
        order.assert_editable();

        const options = {
            ...opts,
        };

        if ("price_unit" in vals) {
            merge = false;
        }

        if (typeof vals.product_id == "number") {
            vals.product_id = this.data.models["product.product"].get(vals.product_id);
        }
        const product = vals.product_id;

        const values = {
            price_type: "price_unit" in vals ? "manual" : "original",
            price_extra: 0,
            price_unit: 0,
            order_id: this.get_order(),
            qty: 1,
            tax_ids: product.taxes_id.map((tax) => ["link", tax]),
            ...vals,
        };

        // Handle refund constraints
        if (
            order.doNotAllowRefundAndSales() &&
            order._isRefundOrder() &&
            (!values.qty || values.qty > 0)
        ) {
            this.dialog.add(AlertDialog, {
                title: _t("Refund and Sales not allowed"),
                body: _t("It is not allowed to mix refunds and sales"),
            });
            return;
        }


        if (values.product_id.isConfigurable() && configure) {
            const payload = await this.openConfigurator(values.product_id);

            if (payload) {
                const productFound = this.models["product.product"]
                    .filter((p) => p.raw?.product_template_variant_value_ids?.length > 0)
                    .find((p) =>
                        p.raw.product_template_variant_value_ids.every((v) =>
                            payload.attribute_value_ids.includes(v)
                        )
                    );

                Object.assign(values, {
                    attribute_value_ids: payload.attribute_value_ids
                        .filter((a) => {
                            if (productFound) {
                                const attr =
                                    this.data.models["product.template.attribute.value"].get(a);
                                return (
                                    attr.is_custom || attr.attribute_id.create_variant !== "always"
                                );
                            }
                            return true;
                        })
                        .map((id) => [
                            "link",
                            this.data.models["product.template.attribute.value"].get(id),
                        ]),
                    custom_attribute_value_ids: Object.entries(payload.attribute_custom_values).map(
                        ([id, cus]) => {
                            return [
                                "create",
                                {
                                    custom_product_template_attribute_value_id:
                                        this.data.models["product.template.attribute.value"].get(
                                            id
                                        ),
                                    custom_value: cus,
                                },
                            ];
                        }
                    ),
                    price_extra: values.price_extra + payload.price_extra,
                    qty: payload.qty || values.qty,
                    product_id: productFound || values.product_id,
                });
            } else {
                return;
            }
        } else if (values.product_id.product_template_variant_value_ids.length > 0) {
            const priceExtra = values.product_id.product_template_variant_value_ids
                .filter((attr) => attr.attribute_id.create_variant !== "always")
                .reduce((acc, attr) => acc + attr.price_extra, 0);
            values.price_extra += priceExtra;
        }

        if (values.product_id.isCombo() && configure) {
            const payload = await makeAwaitable(this.dialog, ComboConfiguratorPopup, {
                product: values.product_id,
            });

            if (!payload) {
                return;
            }

            const comboPrices = computeComboItems(
                values.product_id,
                payload,
                order.pricelist_id,
                this.data.models["decimal.precision"].getAll(),
                this.data.models["product.template.attribute.value"].getAllBy("id")
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
                    order_id: order,
                    qty: 1,
                    attribute_value_ids: comboItem.attribute_value_ids?.map((attr) => [
                        "link",
                        attr,
                    ]),
                    custom_attribute_value_ids: Object.entries(
                        comboItem.attribute_custom_values
                    ).map(([id, cus]) => {
                        return [
                            "create",
                            {
                                custom_product_template_attribute_value_id:
                                    this.data.models["product.template.attribute.value"].get(id),
                                custom_value: cus,
                            },
                        ];
                    }),
                },
            ]);
        }

        const code = opts.code;
        if (values.product_id.isTracked() && (configure || code)) {
            let pack_lot_ids = {};
            const packLotLinesToEdit =
                (!values.product_id.isAllowOnlyOneLot() &&
                    this.get_order()
                        .get_orderlines()
                        .filter((line) => !line.get_discount())
                        .find((line) => line.product_id.id === values.product_id.id)
                        ?.getPackLotLinesToEdit()) ||
                [];

            if (code && code.type === "lot") {
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

        if (values.product_id.to_weight && this.config.iface_electronic_scale && configure) {

            if (values.product_id.isScaleAvailable) {
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
            } else {
                await values.product_id._onScaleNotAvailable();
            }
        }

        if (!values.product_id.isCombo() && vals.price_unit === undefined) {
            values.price_unit = values.product_id.get_price(order.pricelist_id, values.qty);
        }
        const isScannedProduct = opts.code && opts.code.type === "product";
        if (values.price_extra && !isScannedProduct) {
            const price = values.product_id.get_price(
                order.pricelist_id,
                values.qty,
                values.price_extra
            );

            values.price_unit = price;
        }

        const line = this.data.models["pos.order.line"].create({ ...values, order_id: order });
        line.setOptions(options);
        this.selectOrderLine(order, line);
        if (configure) {
            this.numberBuffer.reset();
        }
        const selectedOrderline = order.get_selected_orderline();
        if (options.draftPackLotLines && configure) {
            selectedOrderline.setPackLotLines({
                ...options.draftPackLotLines,
                setQuantity: options.quantity === undefined,
            });
        }

        let to_merge_orderline;
        for (const curLine of order.lines) {
            if (curLine.id !== line.id) {
                if (curLine.can_be_merged_with(line)) {
                    to_merge_orderline = curLine;
                }
            }
        }

        if (to_merge_orderline) {
            to_merge_orderline.merge(line);
            line.delete();
            this.selectOrderLine(order, to_merge_orderline);
        } else if (!selectedOrderline) {
            this.selectOrderLine(order, order.get_last_orderline());
        }

        if (configure) {
            this.numberBuffer.reset();
        }

        order.recomputeOrderData();

        if (configure) {
            this.numberBuffer.reset();
        }

        this.hasJustAddedProduct = true;
        clearTimeout(this.productReminderTimeout);
        this.productReminderTimeout = setTimeout(() => {
            this.hasJustAddedProduct = false;
        }, 3000);

        return line;
    }
});
