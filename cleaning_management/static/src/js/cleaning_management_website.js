/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class CleaningBookingForm extends Interaction {
    static selector = "#cleaning_booking_form";
    dynamicContent = {
        "#cleaning_date": { "t-on-change": this.onChangeDate },
        "#cleaning_time": { "t-on-change": this.onChangeTime },
    };

    get teamSelect() {
        return this.el.querySelector("#cleaning_team_id");
    }

    blankOption() {
        const option = document.createElement("option");
        option.value = "";
        return option;
    }

    onChangeDate() {
        this.el.querySelector("#cleaning_time").value = "";
        this.teamSelect.replaceChildren(this.blankOption());
    }

    async onChangeTime(ev) {
        const time = ev.target.value;
        const date = this.el.querySelector("#cleaning_date").value;
        this.teamSelect.replaceChildren(this.blankOption());
        if (!time) {
            return;
        }
        if (!date) {
            this.services.notification.add(
                "Please choose a cleaning date.", { type: "warning" }
            );
            ev.target.value = "";
            return;
        }
        const teams = await this.waitFor(
            rpc("/cleaning/available_teams", {
                cleaning_date: date,
                cleaning_time: time,
            })
        );
        for (const team of teams) {
            const option = document.createElement("option");
            option.value = team.id;
            option.textContent = team.name;
            this.teamSelect.appendChild(option);
        }
    }
}

registry
    .category("public.interactions")
    .add("cleaning_management.booking_form", CleaningBookingForm);