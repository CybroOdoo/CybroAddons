/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

/**
 * ProductsPopup - shows multi-variant attributes and values for a product.
 * Extends AbstractAwaitablePopup so the caller can await the user's choice.
 */
export class ProductsPopup extends AbstractAwaitablePopup {
    static template = "pos_multi_variant.ProductsPopup";
    static defaultProps = {
        confirmText: _t("Confirm"),
        cancelText: _t("Cancel"),
        title: _t("Product"),
        products: [],
        variant_details: [],
        product_tmpl_id: 0,
    };

    setup() {
        super.setup();
        this.pos = usePos();
        // Plain object so OWL reactive proxy can track key assignments
        this.state = useState({ selectedVariants: {} });
    }

    /**
     * Called when the user clicks a variant card.
     * @param {Object} product  - the variants.tree record (has attribute_id, extra_price, value_ids)
     * @param {Object} variant  - the product.attribute.value record (has id, name)
     * @param {string} attrName - the attribute display name (pre-resolved from template)
     */
    selectVariant(product, variant, attrName) {
        this.state.selectedVariants[attrName] = {
            type: variant.name,
            extra_price: product.extra_price,
        };
    }

    /**
     * Returns true if the given variant is currently selected for the given attribute.
     */
    isSelected(attrName, variantName) {
        return this.state.selectedVariants[attrName]?.type === variantName;
    }

    /**
     * Called by AbstractAwaitablePopup.confirm() — returns the list of selected variants.
     */
    getPayload() {
        return Object.values(this.state.selectedVariants);
    }

    /**
     * Returns the product thumbnail URL for display inside the popup.
     */
    imageUrl() {
        return `/web/image?model=product.product&field=image_128&id=${this.props.product_tmpl_id}&unique=1`;
    }
}
