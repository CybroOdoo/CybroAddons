/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class ReturnForm extends Interaction {
    static selector = ".sale_return";
    dynamicContent = {
        ".js_add_json": {
            "t-on-click.prevent": this._validation,
        },
        ".sale_return_form": {
            "t-on-submit.prevent": this._submission,
        },
    };

    // Validate quantity based on user interaction
    _validation(ev) {
        const link = ev.currentTarget;
        const input = link.closest(".input-group")?.querySelector("input.quantity");
        if (!input) {
            return;
        }
        const min = parseFloat(input.dataset.min || 0);
        const max = parseFloat(input.dataset.max || Infinity);
        const previousQty = parseFloat(input.value || 0);
        const isMinus = link.getAttribute("aria-label") === "Remove one" || link.getAttribute("title") === "Remove one" || !!link.querySelector(".fa-minus, [data-icon='minus'], [data-icon='remove']");
        const quantity = (isMinus ? -1 : 1) + previousQty;
        const newQty = quantity > min ? (quantity < max ? quantity : max) : min;
        if (newQty !== previousQty) {
            input.value = newQty;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        }
    }

    // Handle form submission
    async _submission(ev) {
        const val = [];
        const rows = this.el.querySelectorAll("tr.order_line");
        rows.forEach((row) => {
            const input = row.querySelector(".quantity");
            const reasonEl = row.querySelector("#return_reason");
            if (input) {
                const qty = parseFloat(input.value || 0);
                if (qty > 0) {
                    const deliveredQty = input.dataset.delivered_qty || input.dataset.deliveredQty || input.getAttribute("data-delivered_qty") || input.getAttribute("data-delivered-qty") || 0;
                    val.push({
                        order_id: input.dataset.orderId || input.getAttribute("data-order-id"),
                        line_id: input.dataset.lineId || input.getAttribute("data-line-id"),
                        deli_qty: deliveredQty,
                        quantity: qty,
                        product_id: input.dataset.productId || input.getAttribute("data-product-id"),
                        reason: reasonEl ? reasonEl.value : "",
                    });
                }
            }
        });

        if (val.length !== 0) {
            const result = await rpc("/sale_return", { vals: val });
            if (result === true) {
                window.location.href = "/my/request-thank-you";
            } else {
                alert("Retry again");
            }
        } else {
            alert("Please specify at least one return quantity");
        }
    }
}

registry.category("public.interactions").add("website_multi_product_return_management.return_form", ReturnForm);

