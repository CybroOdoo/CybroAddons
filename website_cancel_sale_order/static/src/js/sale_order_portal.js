/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";

export class WebsiteSaleOrderCancel extends Interaction {
    static selector = ".editReasonForm";

    start() {
        const submitButton = this.el.querySelector("#submit_button");
        if (submitButton) {
            submitButton.addEventListener("click", this._onSubmit.bind(this));
        }
    }

    _onSubmit(e) {
        e.preventDefault();
        var reason = this.el.querySelector("#reason").value || "";
        var sale_order_id = this.el.querySelector("#sale_order_id").value;
        var accessTokenEl = this.el.querySelector("#access_token");
        var access_token = accessTokenEl ? accessTokenEl.value : null;

        if (reason.trim() === "") {
            alert("Please specify the reason properly");
            return;
        }

        rpc("/cancel/reason/edit", {
            'reason': reason,
            'sale_order_id': sale_order_id,
            'access_token': access_token,
        }).then(function(result) {
            if (result && result.error) {
                alert(result.error);
                return;
            }
            location.reload();
        });
    }
}

registry
    .category("public.interactions")
    .add("website_cancel_sale_order.sale_order_cancel", WebsiteSaleOrderCancel);
