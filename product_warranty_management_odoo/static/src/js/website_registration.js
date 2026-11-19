import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/**
 * Load the warranty products of the selected sale order into the product
 * select of the website warranty claim form.
 */
export class WarrantyClaim extends Interaction {
    static selector = ".o_warranty_claim form";
    dynamicContent = {
        "#sale_order_id": { "t-on-change": this.onChangeSaleOrder },
    };

    async willStart() {
        if (this.el.querySelector("#sale_order_id").value) {
            await this.onChangeSaleOrder();
        }
    }

    async onChangeSaleOrder() {
        const orderId = parseInt(this.el.querySelector("#sale_order_id").value);
        const productEl = this.el.querySelector("#product_id");
        productEl.replaceChildren(new Option(_t("Select a product"), ""));
        productEl.disabled = true;
        if (!orderId) {
            return;
        }
        const products = await this.waitFor(
            rpc("/warranty/products", { order_id: orderId })
        );
        for (const product of products) {
            productEl.add(new Option(product.name, product.id));
        }
        productEl.disabled = !products.length;
    }
}

registry
    .category("public.interactions")
    .add("product_warranty_management_odoo.warranty_claim", WarrantyClaim);
