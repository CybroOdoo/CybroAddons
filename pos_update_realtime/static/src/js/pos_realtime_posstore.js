/** @odoo-module */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.busService = this.env.services.bus_service;
        this.channel = String(this.session.id);
        await this.busService.addChannel(this.channel);
        this.busService.subscribe("product_update", this._onBusNotification.bind(this));
    },

    _onBusNotification(event) {
        const notifications = event.notification || event;
        if (notifications.product_id) {
            this._handleProductUpdate(notifications);
        }
    },

    async _handleProductUpdate(productData) {
        const productModel = this.models["product.product"];
        if (!productModel) return;
        const product = productModel.get(productData.product_id);
        if (product) {
            // Resolve taxes_id to actual model objects (not raw IDs) so that
            // Orderline.lineScreenValues can access tax.tax_group_id.pos_receipt_label
            // without a TypeError.
            const taxModel = this.models["account.tax"];
            const resolvedTaxes = taxModel
                ? (productData.taxes_id || [])
                    .map(t => taxModel.get(Number(t)))
                    .filter(Boolean)
                : product.taxes_id; // fallback: keep existing taxes if model not available

            Object.assign(product, {
                display_name: productData.name,
                lst_price: productData.list_price,
                standard_price: productData.standard_price,
                qty_available: productData.qty_available,
                barcode: productData.barcode,
                categ_id: productData.categ_id,
                taxes_id: resolvedTaxes,
            });

            // Update prices on existing orderlines in all ongoing orders
            const updatedCount = this._updateOrderlinesForProduct(productData);

            const msg =
                updatedCount > 0
                    ? `Product "${productData.name}" updated – ${updatedCount} orderline(s) refreshed`
                    : `Product "${productData.name}" updated`;

            this.env.services.notification.add(msg, { type: "info" });
            this.env.bus.trigger("PRODUCT_UPDATED");
        } else {
            await this._loadNewProduct(productData.product_id);
        }
    },

    /**
     * Update the unit price of existing orderlines for the given product
     * in all non-finalized (ongoing) orders.
     *
     * Rules:
     *  - Skip finalized orders (state !== "draft", i.e. paid/posted).
     *  - Skip orderlines whose price was manually overridden by the cashier
     *    (price_type === "manual").
     *
     * @param {Object} productData  The bus notification payload.
     * @returns {number}            Number of orderlines that were updated.
     */
    _updateOrderlinesForProduct(productData) {
        const orderModel = this.models["pos.order"];
        if (!orderModel) return 0;

        let updatedCount = 0;

        for (const order of orderModel.getAll()) {
            // Only touch orders still in progress (state === "draft")
            if (order.finalized) continue;

            for (const line of order.lines) {
                // Match lines that belong to the updated product
                if (line.product_id?.id !== productData.product_id) continue;

                // Respect manual price overrides set by the cashier
                if (line.price_type === "manual") continue;

                line.setUnitPrice(productData.list_price);
                updatedCount++;
            }
        }

        return updatedCount;
    },

    async _loadNewProduct(productId) {
        try {
            const productData = await this.data.read("product.product", [productId]);
            if (productData.length) {
                this.env.services.notification.add(
                    `New product added to POS`,
                    { type: "success" }
                );
                this.env.bus.trigger("PRODUCT_UPDATED");
            }
        } catch (err) {
            // silently ignore – the product simply isn't available in this session yet
        }
    },
});
