import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";
import { formatCurrency } from "@web/core/currency";

patch(PosOrderline.prototype, {
    get bundleDetails() {
        if (this.product_id?.is_bundle && this.product_id?.bundle_contents_info) {
            try {
                const rawInfo = this.product_id.bundle_contents_info;
                const details = typeof rawInfo === "string" ? JSON.parse(rawInfo) : rawInfo;
                const currencyId = this.currency?.id || this.order_id?.currency?.id || this.order_id?.config_id?.currency_id?.id;
                return (details || []).map((item) => {
                    const qty = Number(item.qty);
                    const formattedQty = Number.isInteger(qty) ? qty : item.qty;
                    return {
                        ...item,
                        qty: formattedQty,
                        uom: item.uom || "Units",
                        formattedPrice: formatCurrency(item.price, currencyId),
                    };
                });
            } catch (e) {
                console.error("Error parsing bundle details", e);
                return [];
            }
        }
        return [];
    },
});

