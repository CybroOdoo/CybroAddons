/** @odoo-module **/
import {formView} from '@web/views/form/form_view';
import {registry} from "@web/core/registry";
import {FormController} from "@web/views/form/form_controller";
import { onMounted, onWillUnmount } from "@odoo/owl";

export class MasterSearch extends FormController {
    get modelParams() {
        const params = super.modelParams;
        if (params && params.config) {
            params.config.mode = "edit";
        }
        return params;
    }

    setup() {
        super.setup();
        this.display = { ...this.display, controlPanel: false };
        this.onRootClick = this.onRootClick.bind(this);
        this.onRootChange = this.onRootChange.bind(this);

        onMounted(() => {
            const root = this.rootRef();
            if (root) {
                root.addEventListener("click", this.onRootClick);
                root.addEventListener("change", this.onRootChange);
            }
        });

        onWillUnmount(() => {
            const root = this.rootRef();
            if (root) {
                root.removeEventListener("click", this.onRootClick);
                root.removeEventListener("change", this.onRootChange);
            }
        });
    }

    onRootClick(ev) {
        const tile = ev.target.closest(".expand_tile");
        if (tile) {
            const resultDiv = tile.closest(".oe_result_div");
            if (resultDiv) {
                const element = resultDiv.querySelector(".oe_details_list");
                if (element) {
                    element.classList.remove("d-none");
                    if (element.style.display === "block") {
                        element.style.display = "none";
                    } else {
                        element.style.display = "block";
                    }
                }
            }
        }
    }

    onRootChange(ev) {
        const radio = ev.target.closest(".o_radio_input");
        if (!radio) {
            return;
        }
        const targetEl = radio.dataset.value;
        const root = this.rootRef() || document;
        const searchTabs = root.querySelectorAll(".oe_search_tab");

        const searchByOptions = [
            "customer",
            "product",
            "transaction details",
            "sale details",
            "purchase details",
            "account details",
            "any",
        ];
        if (!searchByOptions.includes(targetEl)) {
            return;
        }

        const treeEls = root.querySelectorAll(".oe_details_list");
        treeEls.forEach((element) => {
            element.style.display = "none";
            element.classList.remove("d-none");
        });

        switch (targetEl) {
            case "customer":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#customer_search_results")?.classList.remove("d-none");
                break;
            case "product":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#product_search_results")?.classList.remove("d-none");
                break;
            case "transaction details":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#inventory_search_results")?.classList.remove("d-none");
                break;
            case "sale details":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#sale_search_results")?.classList.remove("d-none");
                break;
            case "purchase details":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#purchase_search_results")?.classList.remove("d-none");
                break;
            case "account details":
                searchTabs.forEach((el) => {
                    el.classList.add("d-none");
                });
                root.querySelector("#accounting_search_results")?.classList.remove("d-none");
                break;
            case "any":
                searchTabs.forEach((el) => {
                    el.classList.remove("d-none");
                });
                break;
        }
        root.querySelector("#recent_searches")?.classList.remove("d-none");
    }
}

export const MasterSearchClass = {
    ...formView,
    Controller: MasterSearch,
};
registry.category("views").add("master_search", MasterSearchClass);

