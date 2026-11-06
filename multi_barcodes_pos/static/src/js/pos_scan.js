/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { DebugWidget } from "@point_of_sale/app/utils/debug/debug_widget";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Extend DebugWidget to support multi-barcode product scan.
 */
patch(DebugWidget.prototype, {
    /**
     * Initialize required services.
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    },

    /**
     * Handle barcode scan.
     * Checks custom barcode mapping and adds product to order.
     */
    async barcodeScan() {
        if (!this.barcodeReader) {
            return;
        }

        await this.orm.call(
            'multi.barcode.products',
            'get_barcode_val',
            [this.state.barcodeInput]
        ).then(async (data) => {
            if (data && data[1]) {
                const productId = data[1];
                let product = this.pos.models["product.product"].get(productId);
                if (!product) {
                    await this.pos.loadNewProducts([["id", "=", productId]]);
                    product = this.pos.models["product.product"].get(productId);
                }

                if (product) {
                    await this.pos.addLineToCurrentOrder(
                        {
                            product_id: product,
                            product_tmpl_id: product.product_tmpl_id,
                        },
                        {},
                        product.needToConfigure()
                    );
                } else {
                    this.dialog.add(AlertDialog, {
                        body: _t("Product is not loaded in the POS"),
                    });
                }
            } else {
                await this.barcodeReader.scan(this.state.barcodeInput);
            }
        });
    }
});

/**
 * Extend ProductScreen to support multi-barcode lookup during barcode scan.
 */
patch(ProductScreen.prototype, {
    /**
     * Initialize required services.
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    async _getProductByBarcode(code) {
        let product = await super._getProductByBarcode(...arguments);
        if (!product && code?.base_code) {
            const multiBarcodeRec = this.pos.models["multi.barcode.products"]?.getBy("multi_barcode", code.base_code);
            if (multiBarcodeRec && multiBarcodeRec.product_multi_id) {
                product = multiBarcodeRec.product_multi_id;
            } else if (this.orm) {
                const res = await this.orm.call(
                    'multi.barcode.products',
                    'get_barcode_val',
                    [code.base_code]
                );
                if (res && res[1]) {
                    const productId = res[1];
                    product = this.pos.models["product.product"].get(productId);
                    if (!product) {
                        await this.pos.loadNewProducts([["id", "=", productId]]);
                        product = this.pos.models["product.product"].get(productId);
                    }
                }
            }
        }
        return product;
    }
});


