import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async initServerData() {
        await super.initServerData(...arguments);
        this.data.connectWebSocket("PRODUCT_UPDATE", (payload) => this._handleProductUpdate(payload));
    },

    async _handleProductUpdate(productData) {
        if (!productData || !productData.product_id) {
            return;
        }

        const productModel = this.models["product.product"];
        if (!productModel) {
            return;
        }

        const product = productModel.get(productData.product_id);

        // If product is archived or no longer available in POS, remove it from active session
        if (productData.active === false || productData.available_in_pos === false) {
            const tmplModel = this.models["product.template"];
            const tmpl = product?.product_tmpl_id || (tmplModel && productData.product_tmpl_id ? tmplModel.get(productData.product_tmpl_id) : null);

            let removed = false;
            if (product) {
                product.delete();
                removed = true;
            }

            if (tmpl) {
                const remainingVariants = (tmpl.product_variant_ids || []).filter(
                    (v) => v.id !== productData.product_id && v.active && v.available_in_pos
                );
                if (!remainingVariants.length || productData.tmpl_active === false || productData.available_in_pos === false) {
                    tmpl.delete();
                    removed = true;
                } else if (typeof tmpl.onUpdate === "function") {
                    tmpl.onUpdate();
                }
            }

            if (removed) {
                const notificationService = this.notification || this.env.services.notification;
                if (notificationService) {
                    notificationService.add(
                        _t('Product "%s" is no longer available in POS', productData.name),
                        { type: "warning" }
                    );
                }

                if (this.env.bus) {
                    this.env.bus.trigger("PRODUCT_UPDATED");
                }
            }
            return;
        }

        if (product) {
            const taxModel = this.models["account.tax"];
            const resolvedTaxes = taxModel && productData.taxes_id
                ? productData.taxes_id
                    .map((t) => taxModel.get(Number(t)))
                    .filter(Boolean)
                : product.taxes_id;

            const categModel = this.models["product.category"];
            const resolvedCateg = productData.categ_id && categModel
                ? categModel.get(Number(productData.categ_id))
                : false;

            product.display_name = productData.name;
            product.lst_price = productData.list_price;
            product.standard_price = productData.standard_price;
            if (productData.qty_available !== undefined) {
                product.qty_available = productData.qty_available;
            }
            if (productData.barcode !== undefined) {
                product.barcode = productData.barcode;
            }
            if (productData.default_code !== undefined) {
                product.default_code = productData.default_code;
            }
            if (resolvedCateg) {
                product.categ_id = resolvedCateg;
            }
            if (resolvedTaxes) {
                product.taxes_id = resolvedTaxes;
            }

            product._searchString = null;
            const tmpl = product.product_tmpl_id || (this.models["product.template"] && productData.product_tmpl_id ? this.models["product.template"].get(productData.product_tmpl_id) : null);
            if (tmpl) {
                tmpl.name = productData.tmpl_name || tmpl.name;
                tmpl.list_price = productData.list_price;
                if (resolvedCateg) {
                    tmpl.categ_id = resolvedCateg;
                }
                if (typeof tmpl.onUpdate === "function") {
                    tmpl.onUpdate();
                }
            }

            const updatedCount = this._updateOrderlinesForProduct(productData);

            const notificationService = this.notification || this.env.services.notification;
            const msg =
                updatedCount > 0
                    ? _t('Product "%s" updated – %s orderline(s) refreshed', productData.name, updatedCount)
                    : _t('Product "%s" updated', productData.name);

            if (notificationService) {
                notificationService.add(msg, { type: "info" });
            }

            if (this.env.bus) {
                this.env.bus.trigger("PRODUCT_UPDATED");
            }
        } else {
            await this._loadNewProduct(productData.product_id, productData.product_tmpl_id);
        }
    },

    /**
     * Update the unit price of existing orderlines for the given product
     * in all non-finalized (ongoing) orders respecting pricelists.
     *
     * Rules:
     *  - Skip finalized orders (order.finalized === true).
     *  - Skip orderlines whose price was manually overridden by the cashier
     *    (line.price_type === "manual").
     *  - Recompute unit price using pricelists via recomputeUnitPrice().
     *
     * @param {Object} productData  The bus notification payload.
     * @returns {number}            Number of orderlines that were updated.
     */
    _updateOrderlinesForProduct(productData) {
        const orderModel = this.models["pos.order"];
        if (!orderModel) {
            return 0;
        }

        let updatedCount = 0;

        for (const order of orderModel.getAll()) {
            if (order.finalized) {
                continue;
            }

            for (const line of order.lines) {
                if (line.product_id?.id !== productData.product_id) {
                    continue;
                }

                if (line.price_type === "manual") {
                    continue;
                }

                if (typeof line.recomputeUnitPrice === "function") {
                    line.recomputeUnitPrice();
                } else {
                    line.setUnitPrice(productData.list_price);
                }
                updatedCount++;
            }
        }

        return updatedCount;
    },

    async _loadNewProduct(productId, tmplId) {
        try {
            if (tmplId && !this.models["product.template"]?.get(tmplId)) {
                await this.data.searchRead("product.template", [["id", "=", tmplId]]);
            }
            const productData = await this.data.searchRead("product.product", [["id", "=", productId]]);
            if (productData && productData.length) {
                const loadedProduct = this.models["product.product"]?.get(productId);
                const tmplRecordId = tmplId || (loadedProduct?.product_tmpl_id?.id || productData[0].product_tmpl_id?.[0] || productData[0].product_tmpl_id);
                if (tmplRecordId && !this.models["product.template"]?.get(tmplRecordId)) {
                    await this.data.searchRead("product.template", [["id", "=", tmplRecordId]]);
                }
                const notificationService = this.notification || this.env.services.notification;
                if (notificationService) {
                    notificationService.add(_t("New product added to POS"), { type: "success" });
                }
                if (this.env.bus) {
                    this.env.bus.trigger("PRODUCT_UPDATED");
                }
            }
        } catch (err) {
            console.error("pos_update_realtime: failed to load new product", productId, err);
        }
    },
});
