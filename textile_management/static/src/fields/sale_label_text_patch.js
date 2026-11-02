import { patch } from "@web/core/utils/patch";
import { SaleLabelTextField } from "@sale/js/sale_label_text/sale_label_text";

// In v20 the Description cell of a sale order line is the product picker,
// and it searches with its own domain instead of the product field's one.
patch(SaleLabelTextField.prototype, {
    get productDomain() {
        const domain = super.productDomain;
        if (this.props.record.evalContext.parent?.is_textile_sale_order) {
            return [...domain, ["is_textile_product", "=", true]];
        }
        return domain;
    },
});
