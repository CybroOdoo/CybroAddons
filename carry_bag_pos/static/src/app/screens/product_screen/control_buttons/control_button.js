/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { BagPopup } from "@carry_bag_pos/components/bag_popup/bag_popup";  // Changed path
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(ControlButtons.prototype, {
    async onClickBagCharges() {
        const categoryId = this.pos.config.bag_category_id?.id;

        const allProducts = this.pos.models["product.product"].getAll();

        const bagProducts = allProducts.filter(product =>
            product.pos_categ_ids?.some(c => c.id === categoryId)
        );

        await makeAwaitable(this.dialog, BagPopup, {
            title: _t("Select Bag"),
            products: bagProducts,
        });
    },
});