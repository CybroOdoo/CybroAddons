import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

// Patch the PosOrderline model to include bundleDetails and inject them into getDisplayData()
patch(PosOrderline.prototype, {
    get bundleDetails() {
        if (this.product_id.is_bundle && this.product_id.bundle_contents_info) {
            try {
                return JSON.parse(this.product_id.bundle_contents_info);
            } catch (e) {
                console.error("Error parsing bundle details", e);
                return [];
            }
        }
        return [];
    },

    getDisplayData() {
        const bundleDetailsCopy = this.bundleDetails ? JSON.parse(JSON.stringify(this.bundleDetails)) : [];
        return {
            ...super.getDisplayData(),
            is_bundle: this.product_id.is_bundle,
            bundleDetails: bundleDetailsCopy,
        };
    }
});

// Patch the generic Orderline component props to allow the new bundle fields
patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            type: Object,
            shape: {
                ...Orderline.props.line.shape,
                is_bundle: { type: Boolean, optional: true },
                bundleDetails: { type: Array, optional: true },
            }
        }
    }
});
