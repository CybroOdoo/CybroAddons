/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    getProductStockQty(product) {
        if (!product) {
            return 0;
        }

        const config = this.config || {};
        const stockType = config.stock_product || config.stock_type || "on_hand";
        const stockFrom = config.location_from || config.stock_from || "all_warehouse";
        const rawLocId = config.pos_stock_location_id || config.stock_location_id;

        function extractId(val) {
            if (val === null || val === undefined) return null;
            if (typeof val === "number") return val;
            if (typeof val === "string") {
                const parsed = parseInt(val, 10);
                return isNaN(parsed) ? null : parsed;
            }
            if (Array.isArray(val)) return extractId(val[0]);
            if (typeof val === "object") return extractId(val.id);
            return null;
        }

        const targetLocId = extractId(rawLocId);
        const targetId = extractId(product.id) || extractId(product.raw?.id);

        // Collect all variant IDs for this product template / product variant
        const variantIdsSet = new Set();
        if (targetId) {
            variantIdsSet.add(targetId);
        }

        const rawVariantIds = product.product_variant_ids || product.raw?.product_variant_ids;
        if (Array.isArray(rawVariantIds)) {
            for (const vId of rawVariantIds) {
                const parsed = extractId(vId);
                if (parsed) variantIdsSet.add(parsed);
            }
        }

        const productModel = this.models?.["product.product"];
        if (productModel) {
            const allVariants = productModel.getAll();
            for (const p of allVariants) {
                const pId = extractId(p.id) || extractId(p.raw?.id);
                const pTmplId = extractId(p.product_tmpl_id) || extractId(p.raw?.product_tmpl_id);
                if (targetId && (pId === targetId || pTmplId === targetId)) {
                    if (pId) variantIdsSet.add(pId);
                }
            }
        }
        const variantIds = Array.from(variantIdsSet);

        // 1. On-Hand Stock calculation
        if (stockType === "on_hand") {
            let totalQuant = 0;
            let foundQuant = false;

            const quantModel = this.models?.["stock.quant"];
            if (quantModel) {
                const quants = quantModel.getAll();
                for (const quant of quants) {
                    const qProdId = extractId(quant.product_id) || extractId(quant.raw?.product_id);
                    const qLocId = extractId(quant.location_id) || extractId(quant.raw?.location_id);

                    if (qProdId && variantIds.includes(qProdId)) {
                        if (stockFrom === "all_warehouse" || !targetLocId || qLocId === targetLocId) {
                            const val = quant.quantity ?? quant.available_quantity ?? quant.raw?.quantity ?? quant.raw?.available_quantity ?? 0;
                            totalQuant += Number(val);
                            foundQuant = true;
                        }
                    }
                }
            }

            if (foundQuant) {
                return totalQuant;
            }

            // 2. Sum qty_available across product variants
            if (productModel && variantIds.length > 0) {
                const variants = productModel.getAll().filter((p) => variantIds.includes(extractId(p.id)));
                let vSum = 0;
                let foundVariantVal = false;
                for (const v of variants) {
                    const vVal = v.qty_available ?? v.raw?.qty_available;
                    if (typeof vVal === "number" && !isNaN(vVal)) {
                        vSum += Number(vVal);
                        foundVariantVal = true;
                    }
                }
                if (foundVariantVal) {
                    return vSum;
                }
            }

            // 3. Direct template qty_available property fallback
            let qty = product.qty_available ?? product.raw?.qty_available ?? product.product_tmpl_id?.qty_available;
            if (typeof qty === "number" && !isNaN(qty)) {
                return qty;
            }

            return 0;
        }

        // 2. Incoming Stock calculation
        if (stockType === "incoming_qty") {
            let totalLine = 0;
            let foundLine = false;
            const moveLineModel = this.models?.["stock.move.line"];
            if (moveLineModel) {
                const lines = moveLineModel.getAll();
                for (const line of lines) {
                    const lProdId = extractId(line.product_id) || extractId(line.raw?.product_id);
                    const destLocId = extractId(line.location_dest_id) || extractId(line.raw?.location_dest_id);

                    if (lProdId && variantIds.includes(lProdId)) {
                        if (stockFrom === "all_warehouse" || !targetLocId || destLocId === targetLocId) {
                            totalLine += Number(line.quantity ?? line.raw?.quantity ?? 0);
                            foundLine = true;
                        }
                    }
                }
            }
            if (foundLine) {
                return totalLine;
            }
            return product.incoming_qty ?? product.raw?.incoming_qty ?? 0;
        }

        // 3. Outgoing Stock calculation
        if (stockType === "outgoing_qty") {
            let totalLine = 0;
            let foundLine = false;
            const moveLineModel = this.models?.["stock.move.line"];
            if (moveLineModel) {
                const lines = moveLineModel.getAll();
                for (const line of lines) {
                    const lProdId = extractId(line.product_id) || extractId(line.raw?.product_id);
                    const srcLocId = extractId(line.location_id) || extractId(line.raw?.location_id);

                    if (lProdId && variantIds.includes(lProdId)) {
                        if (stockFrom === "all_warehouse" || !targetLocId || srcLocId === targetLocId) {
                            totalLine += Number(line.quantity ?? line.raw?.quantity ?? 0);
                            foundLine = true;
                        }
                    }
                }
            }
            if (foundLine) {
                return totalLine;
            }
            return product.outgoing_qty ?? product.raw?.outgoing_qty ?? 0;
        }

        return product.qty_available ?? product.raw?.qty_available ?? 0;
    },
});
