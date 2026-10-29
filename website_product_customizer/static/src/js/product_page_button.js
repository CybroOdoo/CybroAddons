/** @odoo-module **/

/**
 * Keeps the "Customize & Design" button href in sync with the currently
 * selected product variant on the product page.
 *
 * When the user changes variant attributes (color, size, etc.) the standard
 * website_sale JS updates input.product_id.  We listen for that change and
 * append ?variant_id=<id> to the designer button link so the designer opens
 * with the correct variant pre-selected.
 */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class DesignerButtonVariant extends Interaction {
    static selector = "#product_detail";

    dynamicContent = {
        "input.product_id": {
            "t-on-change": this._onVariantChange,
        },
    };

    setup() {
        this._updateDesignerButton();
    }

    _onVariantChange() {
        this._updateDesignerButton();
    }

    _updateDesignerButton() {
        const btn = this.el.querySelector("#o_designer_btn_link");
        if (!btn) return;

        const productIdInput = this.el.querySelector("input.product_id");
        if (!productIdInput) return;

        const variantId = parseInt(productIdInput.value) || 0;
        const tmplId = btn.dataset.productTmplId;
        const baseHref = "/shop/designer/" + tmplId;

        if (variantId) {
            btn.setAttribute("href", baseHref + "?variant_id=" + variantId);
        } else {
            btn.setAttribute("href", baseHref);
        }
    }
}

registry
    .category("public.interactions")
    .add(
        "website_product_customizer.DesignerButtonVariant",
        DesignerButtonVariant
    );
