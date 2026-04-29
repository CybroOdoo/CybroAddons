/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { LotListPopup } from "./EditListPopup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
    async editLots(product, packLotLinesToEdit) {
        let stockLots = this.models['stock.lot'].getAll();
        var st = stockLots.filter(line => (line.product_id?.id || line.product_id) == product.id)
        const payload = await makeAwaitable(this.dialog, LotListPopup, {
            title: _t("Lot/Serial Number(s) Required"),
            name: product.display_name,
            lotStock: st
        });
        if (!payload) {
            return null;
        }
        if (payload.newArray.length != 0) {
            const lot_expiry_check = await this.data.call("product.product",
                "lot_expiry_check", [product.id, payload.newArray[0].text]);
            if (lot_expiry_check == 0) {
                this.dialog.add(AlertDialog, {
                    title: _t("There is no such Lot/serial number"),
                    body: _t("Please Select a Valid Lot/Serial number"),
                });
                return null;
            }
            else if (lot_expiry_check[0] === 2) {
                if (lot_expiry_check[1]) {
                    this.dialog.add(AlertDialog, {
                        title: _t("Expiration Alert"),
                        body: _t("The Lot/Serial number is expired on " + lot_expiry_check[1]),
                    });
                }
                return null;
            } else if (lot_expiry_check[0] === 1) {
                this.dialog.add(AlertDialog, {
                    title: _t("Expiry Warning"),
                    body: _t("The selected Lot/Serial number will expire soon."),
                });
            }
            const modifiedPackLotLines = Object.fromEntries(
                payload.newArray.filter((item) => item.id).map((item) => [item.id, item.text])
            );
            const newPackLotLines = payload.newArray
                .filter((item) => !item.id)
                .map((item) => ({ lot_name: item.text }));

            return { modifiedPackLotLines, newPackLotLines };
        }
    },
});
