import { ScaleScreen } from "./scale_screen";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

patch(PosStore.prototype, {
    async handleWeighableProduct(values, order, configure) {
        if (
            this.config.is_allow_manual_weight &&
            (values.product_tmpl_id?.to_weight || values.product_id?.to_weight) &&
            configure
        ) {
            let productPrice = 0;
            const overridedValues = {};
            if (order?.pricelist_id) {
                overridedValues.pricelist = order.pricelist_id;
            }
            if (order?.fiscal_position_id) {
                overridedValues.fiscalPosition = order.fiscal_position_id;
            }

            if (values.product_id?.getTaxDetails) {
                productPrice =
                    values.product_id.getTaxDetails({ overridedValues })?.total_included ?? 0;
            } else if (values.product_id?.getPrice) {
                productPrice = values.product_id.getPrice(
                    order?.pricelist_id,
                    1,
                    values.price_extra || 0
                );
            } else if (values.price_unit) {
                productPrice = values.price_unit;
            } else {
                productPrice = values.product_tmpl_id?.list_price || 0;
            }

            const scaleData = {
                productName: values.product_tmpl_id?.display_name || values.product_id?.display_name,
                uomName: values.product_tmpl_id?.uom_id?.name || 'Kg',
                uomRounding: values.product_tmpl_id?.uom_id?.rounding || 0.01,
                productPrice: productPrice,
            };

            const weight = await makeAwaitable(
                this.env.services.dialog,
                ScaleScreen,
                scaleData
            );

            if (weight && weight > 0) {
                values.qty = weight;
                return true;
            }
            return false;
        }

        return super.handleWeighableProduct(values, order, configure);
    },
});
