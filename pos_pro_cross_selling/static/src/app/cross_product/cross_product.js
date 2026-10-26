/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { Component, proxy, useProps, t } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CrossProduct extends Component {
    static components = { Dialog };
    static template = "pos_pro_cross_selling.CrossProduct";
    props = useProps({
        product: t.array().optional([]),
        closePopup: t.string().optional(_t("Cancel")),
        confirmPopup: t.string().optional(_t("Confirm")),
        close: t.function().optional(),
    });

    setup() {
        super.setup();
        const initialProducts = (this.props.product || []).map(p => ({
            ...p,
            selected: Boolean(p.selected)
        }));
        this.state = proxy({
            Products: initialProducts,
        });
    }
    async confirm() {
        // Adding Products into the order line
        const products = this.state.Products;
        const pos = this.env.services.pos;

        for (const product of products) {
            if (product.selected) {
                // Get the product variant from POS models
                const selectedProduct = pos.models["product.product"].get(product.id);

                if (selectedProduct && selectedProduct.product_tmpl_id) {
                    await pos.addLineToCurrentOrder({
                        product_tmpl_id: selectedProduct.product_tmpl_id,
                        product_id: selectedProduct
                    }, {});
                }
            }
        }
        this.props.close();
    }
    _onClickOrder(event, product) {
        const p = this.state.Products.find(item => item.id === product.id);
        if (p) {
            p.selected = !p.selected;
            this.state.Products = [...this.state.Products];
        }
    }
}
