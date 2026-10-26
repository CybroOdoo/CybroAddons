import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

// Fields shown for each request type; every other field group stays hidden.
const FIELDS_BY_TYPE = {
    extra_pickup: ["field_category", "field_requested_date"],
    container_swap: ["field_container_type", "field_requested_date"],
    missed_collection: ["field_requested_date"],
    service_hold: ["field_service_hold_dates"],
};
const ALL_FIELDS = [
    "field_category",
    "field_container_type",
    "field_requested_date",
    "field_service_hold_dates",
];

export class ServiceRequestForm extends Interaction {
    static selector = "#request_type";
    dynamicContent = {
        _root: { "t-on-change": this.onTypeChange },
    };

    start() {
        this.toggleFields(this.el.value);
    }

    onTypeChange() {
        this.toggleFields(this.el.value);
    }

    toggleFields(type) {
        const visible = FIELDS_BY_TYPE[type] || FIELDS_BY_TYPE.missed_collection;
        for (const id of ALL_FIELDS) {
            document.getElementById(id)?.classList.toggle("d-none", !visible.includes(id));
        }
    }
}

export class ConfirmCancelRequest extends Interaction {
    static selector = ".js_confirm_cancel";
    dynamicContent = {
        _root: { "t-on-click": this.onClick },
    };

    onClick(ev) {
        if (!window.confirm(this.el.dataset.confirmMessage)) {
            ev.preventDefault();
        }
    }
}

registry.category("public.interactions").add("wm_contracts_billing.service_request_form", ServiceRequestForm);
registry.category("public.interactions").add("wm_contracts_billing.confirm_cancel_request", ConfirmCancelRequest);
