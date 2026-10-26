import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { BagPopup } from "@carry_bag_pos/components/bag_popup/bag_popup";
import { _t } from "@web/core/l10n/translation";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(ControlButtons.prototype, {
    /**
     * Product templates of the POS bag category. In Odoo 20 the POS categories
     * (`pos_categ_ids`) are loaded on `product.template`, so the filter is
     * done on the templates.
     */
    getBagProducts() {
        const categoryId = this.pos.config.bag_category_id?.id;
        if (!categoryId) {
            return [];
        }
        return this.pos.models["product.template"]
            .getAll()
            .filter(
                (template) =>
                    template.available_in_pos &&
                    template.pos_categ_ids?.some((categ) => categ.id === categoryId)
            );
    },

    /**
     * Quantity on hand of the given bag templates, as {template id: quantity}.
     * Returns an empty object when the server cannot be reached (offline).
     */
    async getBagStock(templates) {
        if (!templates.length) {
            return {};
        }
        try {
            return await this.pos.data.call("pos.config", "get_bag_stock", [
                [this.pos.config.id],
                templates.map((template) => template.id),
            ]);
        } catch {
            return {};
        }
    },

    async onClickBagCharges() {
        if (!this.pos.config.bag_category_id) {
            return;
        }
        const templates = this.getBagProducts();
        const stock = await this.getBagStock(templates);
        const template = await makeAwaitable(this.dialog, BagPopup, {
            title: _t("Available Bags"),
            bags: templates.map((bagTemplate) => ({
                template: bagTemplate,
                stock: stock[bagTemplate.id],
            })),
        });
        if (!template || !(await this.pos.canAddProductToCurrentOrder(template))) {
            return;
        }
        // Use the standard flow so that pricelist, taxes, fiscal position
        // and product configuration are handled like any other product.
        await this.pos.addLineToCurrentOrder({ product_tmpl_id: template });
    },
});
