/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductProduct } from "@point_of_sale/app/models/product_product";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        const multiBarcodes = loadedData['multi.barcode.products'] || [];
        const productModel = this.models["product.product"];

        // Ensure barcode index object exists
        if (!productModel.indexedRecords.by.barcode) {
            productModel.indexedRecords.by.barcode = {};
        }
        const barcodeIndex = productModel.indexedRecords.by.barcode;

        for (const multi of multiBarcodes) {
            if (multi.multi_barcode && multi.product_id) {
                // map barcode string to product object
                const productId = typeof multi.product_id === 'object' ? multi.product_id[0] : multi.product_id;
                const product = productModel.get(productId);
                if (product) {
                    barcodeIndex[multi.multi_barcode] = product;
                }
            }
        }
    },
});

patch(ProductProduct.prototype, {
    get searchString() {
        const result = super.searchString;
        let extraBarcodes = "";
        if (this.product_multi_barcodes_ids && this.product_multi_barcodes_ids.length > 0) {
            // Find the multi barcode objects in the store using the IDs
            const multiBarcodeObjects = (this.pos?.product_by_lot || []).filter(
                (mb) => this.product_multi_barcodes_ids.includes(mb.id)
            );
            extraBarcodes = multiBarcodeObjects.map((m) => m.multi_barcode).filter(Boolean).join(" ");
        }
        return extraBarcodes ? `${result} ${extraBarcodes}` : result;
    },
});