/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
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
            order_id: order,
            qty: order.preset_id?.is_return ? -1 : 1,
            tax_ids: productTemplate.taxes_id.map((tax) => ["link", tax]),
            product_id: productTemplate.product_variant_ids[0],
            ...vals,
        };
        if (order.isSaleDisallowed(values, options) && !opts.force) {
            this.dialog.add(AlertDialog, {
                title: _t("Oops.."),
                body: _t("Ensure you validate the refund before taking another order."),
            });
            return;
        }
        let keepGoing = await this.handleConfigurableProduct(
            values,
            productTemplate,
            opts,
            configure
        );
        if (keepGoing === false) {
            return;
        }
        keepGoing = await this.handleComboProduct(values, order, configure);
        if (keepGoing === false) {
            return;
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
                const ProductId = values.product_id.id;
                let result = await this.env.services.orm.call(
                    "stock.lot",
                    "get_available_lots_for_pos",
                    [],
                    { product_id: ProductId }
                );
                const modifiedPackLotLines = result[0];
                const newPackLotLines = result.map((item) => ({ lot_name: result[0] }));
                pack_lot_ids = { modifiedPackLotLines, newPackLotLines };
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
                const decimalAccuracy = this.models["decimal.precision"].find(
                    (dp) => dp.name === "Product Unit"
                ).digits;

                const overridedValues = {};
                if (order.pricelist_id) {
                    overridedValues.pricelist = order.pricelist_id;
                }
                if (order.fiscal_position_id) {
                    overridedValues.fiscalPosition = order.fiscal_position_id;
                }

                this.scale.setProduct(
                    values.product_id,
                    decimalAccuracy,
                    values.product_id.getTaxDetails({ overridedValues }).total_included
                );
                const weight = await this.weighProduct();
                if (weight) {
                    values.qty = weight;
                } else if (weight !== null) {
                    return;
                }
            } else {
                await values.product_tmpl_id._onScaleNotAvailable();
            }
        }

        // Handle price unit
        this.handlePriceUnit(values, order, vals.price_unit);

        const line = this.data.models["pos.order.line"].create({ ...values, order_id: order });
        line.setOptions(options);
        this.selectOrderLine(order, line);
        if (configure) {
            this.numberBuffer.reset();
        }
        let selectedOrderline = order.getSelectedOrderline();
        if (options.draftPackLotLines && configure) {
            selectedOrderline.setPackLotLines({
                ...options.draftPackLotLines,
                setQuantity: options.quantity === undefined,
            });
        }

        // Merge orderline if needed
        this.tryMergeOrderline(order, line, merge, selectedOrderline);

        selectedOrderline = order.getSelectedOrderline();
        if (values.product_id.tracking === "lot") {
            const productTemplate = values.product_id.product_tmpl_id;
            const related_lines = [];
            const price = productTemplate.getPrice(
                order.pricelist_id,
                values.qty,
                values.price_extra,
                false,
                values.product_id,
                selectedOrderline,
                related_lines
            );
            related_lines.forEach((line) => line.setUnitPrice(price));
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

        return order.getSelectedOrderline();
    }
});
