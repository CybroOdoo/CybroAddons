/** @odoo-module **/

/**
 * Extend POS control buttons to handle carry bag selection.
 */

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { BagPopup } from "../bag_popup/bag_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(ControlButtons.prototype, {
    async onClickBagCharges() {
        const categoryId = this.pos.config.bag_category_id?.id;

        if (!categoryId) {
            console.warn("No bag category configured in POS settings");
            await makeAwaitable(this.dialog, BagPopup, {
                title: _t("Select Bag"),
                products: [],
            });
            return;
        }

        const allProducts = this.pos.models["product.product"].getAll();

        const bagProducts = allProducts.filter(product => {
            return product.pos_categ_ids && product.pos_categ_ids.some(categ => categ.id === categoryId);
        });
        console.log('bagProductsbagProducts', bagProducts)

        await makeAwaitable(this.dialog, BagPopup, {
            title: _t("Select Bag"),
            products: bagProducts,
        });
    }
});
