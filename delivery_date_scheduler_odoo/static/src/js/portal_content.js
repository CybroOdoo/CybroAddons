import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class DeliveryDateSchedulerWidget extends Interaction {
    static selector = ".delivery_schedule_portal_content";
    dynamicContent = {
        "#delivery_note": {
            "t-on-change": this._onChangeDeliveryNote,
        },
        "#delivery_date": {
            "t-on-change": this._onChangeDeliveryDate,
        },
        "#confirm": {
            "t-on-click": this._onClickConfirm,
        },
    };

    /**
     * getting input data from delivery_note
     */
    _onChangeDeliveryNote(ev) {
        this.input_comment = ev.currentTarget.value;
    }

    /**
     * getting input data from delivery_date and transfer to checking
     */
    _onChangeDeliveryDate(ev) {
        this.input_date = ev.currentTarget.value;
        this.el.querySelector("#error_for_date").innerHTML = "";
        rpc('/delivery_date_schedule', {'date': this.input_date}).then((data) => {
            this.error_value = data.error_value;
            this.min_date = data.min_date;
            this.max_date = data.max_date;
            if (this.error_value == 2) {
                this.el.querySelector("#error_for_date").innerHTML = "*The delivery date must be within " +
                    this.min_date + " and " + this.max_date;
            }
        });
    }

    /**
     * confirming the quotation and updating the value
     */
    _onClickConfirm(ev) {
        if (!this.error_value) {
            this.el.querySelector("#error_for_date").innerHTML = "Please provide the delivery date";
            return false;
        } else if (this.error_value == 2) {
            this.el.querySelector("#error_for_date").innerHTML = "Please provide the delivery date between " +
                this.min_date + " and " + this.max_date;
            return false;
        } else {
            rpc('/confirm_delivery_date_schedule', {
                'id': ev.currentTarget.getAttribute("value"),
                'access_token': ev.currentTarget.dataset.token,
                'date': this.input_date,
                'description': this.input_comment
            }).then(() => window.location = "/my/home");
        }
    }
}

registry
    .category("public.interactions")
    .add("delivery_date_scheduler_odoo.delivery_date_scheduler_widget", DeliveryDateSchedulerWidget);

