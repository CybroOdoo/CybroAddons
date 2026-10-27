/** @odoo-module */

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { CreateProductPopup } from "@all_in_one_pos_kit/create_product/js/create_product_popup";

// "Create Product" button of the product screen: creates a product that is
// available in the POS and makes it show up without leaving the session.
patch(ControlButtons.prototype, {
    onClickCreateProduct() {
        const categories = this.pos.models["pos.category"]
            ? this.pos.models["pos.category"].getAll().map((c) => ({ id: c.id, name: c.name }))
            : [];
        this.dialog.add(CreateProductPopup, {
            categories,
            onConfirm: (vals) => this._createPosProduct(vals),
        });
    },

    async _createPosProduct({ name, price, barcode, categId }) {
        const orm = this.env.services.orm;
        const notification = this.env.services.notification;
        const values = {
            name,
            list_price: price,
            available_in_pos: true,
            sale_ok: true,
        };
        if (barcode) {
            values.barcode = barcode;
        }
        if (categId) {
            values.pos_categ_ids = [[6, 0, [categId]]];
        }
        const [templateId] = await orm.create("product.template", [values]);

        // Try to load the new product into the running session. If that is not
        // possible, reload the POS (unsynced orders are kept in the browser).
        let loaded = false;
        try {
            await this.pos.data.read("product.template", [templateId]);
            loaded = !!this.pos.models["product.template"].get(templateId);
        } catch (e) {
            loaded = false;
        }
        if (loaded) {
            notification.add(_t("Product '%s' created.", name), { type: "success" });
        } else {
            notification.add(_t("Product '%s' created. Reloading the POS...", name), {
                type: "success",
            });
            setTimeout(() => window.location.reload(), 1200);
        }
    },
});
