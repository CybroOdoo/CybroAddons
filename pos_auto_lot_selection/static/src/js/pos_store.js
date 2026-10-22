/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const options = { ...opts };
        let productTemplate = vals.product_tmpl_id;
        if (typeof productTemplate === "number") {
            productTemplate = this.data.models["product.template"].get(productTemplate);
        }
        const product = vals.product_id || productTemplate?.product_variant_ids?.[0];
        const isTracked = productTemplate?.isTracked
            ? productTemplate.isTracked()
            : ["serial", "lot"].includes(product?.tracking || productTemplate?.tracking);

        if (isTracked && !options.code && configure) {
            const productId = typeof product === "number" ? product : product?.id;
            if (productId) {
                const usedLots = (this.models["pos.pack.operation.lot"]?.readAll() || [])
                    .filter(
                        (lot) =>
                            lot.pos_order_line_id?.product_id?.id === productId &&
                            lot.pos_order_line_id?.order_id?.state === "draft" &&
                            lot.lot_name
                    )
                    .map((lot) => lot.lot_name);

                const availableLots = await this.env.services.orm.call(
                    "stock.lot",
                    "get_available_lots_for_pos",
                    [],
                    {
                        product_id: productId,
                        company_id: this.company.id,
                        config_id: this.config.id,
                        used_lots: usedLots,
                    }
                );
                if (availableLots?.length) {
                    options.code = { type: "lot", code: availableLots[0] };
                }
            }
        }
        return super.addLineToOrder(vals, order, options, configure);
    },
});
