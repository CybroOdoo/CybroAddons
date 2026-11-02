import { usePlugin } from "@odoo/owl";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { BootstrapInstance } from "@web/core/utils/bootstrap_plugin";

export class SaleReturn extends Interaction {
    static selector = "#quote_content";
    dynamicContent = {
        "#hidden_box_btn": { "t-on-click": this.onHiddenBoxBtnClick },
        "#product": { "t-on-change": this.onProductChange },
    };

    setup() {
        this.bootstrap = usePlugin(BootstrapInstance);
    }

    onHiddenBoxBtnClick(ev) {
        ev.preventDefault();
        const modalEl = this.el.querySelector("#hidden_box");
        const bsModal = this.bootstrap.getOrCreateInstance(window.Modal, modalEl);
        bsModal.show();
    }

    onProductChange(ev) {
        const submitEl = this.el.querySelector("#submit");
        submitEl.classList.toggle("d-none", ev.currentTarget.value === "none");
    }
}

registry.category("public.interactions").add("website_return_management.SaleReturn", SaleReturn);
