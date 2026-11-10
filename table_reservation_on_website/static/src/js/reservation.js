/** @odoo-module */
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TableReservationBooking extends Interaction {
    static selector = "#table_reservation_page";
    dynamicContent = {
        "#date": {
            "t-on-change": this.onChangeDate,
        },
        "#start_time": {
            "t-on-change": this.onChangeTime,
            "t-on-blur": this.onChangeTime,
        },
        "#end_time": {
            "t-on-change": this.onChangeTime,
            "t-on-blur": this.onChangeTime,
        },
        "form": {
            "t-on-submit": this.onSubmitForm,
        },
        ".close_btn_alert_modal": {
            "t-on-click": this.onClickCloseBtn,
        },
        ".close_btn_time_alert_modal": {
            "t-on-click": this.onClickCloseAlertBtn,
        },
    };

    setup() {
        this.openingHour = null;
        this.closingHour = null;
        this.isLeadTime = false;
        this.reservationLeadTime = 0.0;
    }

    async start() {
        await this._fetchOpeningClosingHours();
    }

    async _fetchOpeningClosingHours() {
        try {
            const result = await rpc("/pos/get_opening_closing_hours", {});
            if (result && !result.error) {
                this.openingHour = result.opening_hour;
                this.closingHour = result.closing_hour;
                this.isLeadTime = result.is_lead_time;
                this.reservationLeadTime = result.reservation_lead_time || 0.0;
            } else if (result && result.error) {
                console.error("Error: ", result.error);
            }
        } catch (error) {
            console.error("Failed to fetch opening and closing hours:", error);
        }
    }

    onChangeDate() {
        const dateInput = this.el.querySelector("#date");
        const dateVal = dateInput ? dateInput.value : "";
        if (!dateVal) {
            return;
        }
        const selectedDate = new Date(dateVal);
        if (isNaN(selectedDate.getTime())) {
            return;
        }
        if (selectedDate.getFullYear() < 1000) {
            return;
        }
        const alertModal = this.el.querySelector("#alert_modal");
        if (selectedDate.getFullYear() > 9999) {
            if (alertModal) {
                const title = alertModal.querySelector(".modal-title");
                if (title) title.textContent = "Invalid Date";
                const body = alertModal.querySelector(".modal-body p");
                if (body) body.textContent = "Invalid Year";
                alertModal.style.display = "block";
            }
            if (dateInput) dateInput.value = "";
            return;
        }
        const currentDate = new Date();
        if (selectedDate.setHours(0, 0, 0, 0) < currentDate.setHours(0, 0, 0, 0)) {
            if (alertModal) {
                alertModal.style.display = "block";
            }
            if (dateInput) dateInput.value = "";
        }
        this.onChangeTime();
    }

    onClickCloseBtn() {
        const alertModal = this.el.querySelector("#alert_modal");
        if (alertModal) {
            alertModal.style.display = "none";
        }
    }

    onChangeTime() {
        const startTimeInput = this.el.querySelector("#start_time");
        const endTimeInput = this.el.querySelector("#end_time");
        const dateInput = this.el.querySelector("#date");
        const dateVal = dateInput ? dateInput.value : "";

        const timeAlertModal = this.el.querySelector("#time_alert_modal");
        if (timeAlertModal) {
            const title = timeAlertModal.querySelector(".modal-title");
            if (title) title.textContent = "Invalid Time";
            const body = timeAlertModal.querySelector(".modal-body p");
            if (body) body.textContent = "Please select a valid booking start and end time.";
        }

        const now = new Date();
        const currentHours = now.getHours().toString().padStart(2, "0");
        const currentMinutes = now.getMinutes().toString().padStart(2, "0");
        const currentTime = `${currentHours}:${currentMinutes}`;

        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const day = String(now.getDate()).padStart(2, "0");
        const formattedDate = `${year}-${month}-${day}`;

        const startVal = startTimeInput ? startTimeInput.value : "";
        const endVal = endTimeInput ? endTimeInput.value : "";

        if (startVal && endVal) {
            const timeToMinutes = (timeStr) => {
                if (!timeStr) return 0;
                const [h, m] = timeStr.split(":").map(Number);
                return h * 60 + m;
            };

            const getLinearMinutes = (timeStr) => {
                const timeMin = timeToMinutes(timeStr);
                if (!this.openingHour || !this.closingHour) {
                    return timeMin;
                }
                const openMin = timeToMinutes(this.openingHour);
                const closeMin = timeToMinutes(this.closingHour);
                if (openMin <= closeMin) {
                    return timeMin;
                } else {
                    if (timeMin >= openMin) {
                        return timeMin;
                    } else if (timeMin <= closeMin) {
                        return timeMin + 24 * 60;
                    }
                    return timeMin;
                }
            };

            const startLinear = getLinearMinutes(startVal);
            const endLinear = getLinearMinutes(endVal);

            if (startLinear >= endLinear) {
                if (timeAlertModal) timeAlertModal.style.display = "block";
                if (startTimeInput) startTimeInput.value = "";
                if (endTimeInput) endTimeInput.value = "";
                return;
            }
        }

        if (!this.openingHour || !this.closingHour) {
            return;
        }

        const openingH = this.openingHour;
        const closingH = this.closingHour;

        let isStartValid = true;
        if (startVal) {
            if (openingH <= closingH) {
                isStartValid = startVal >= openingH && startVal <= closingH;
            } else {
                isStartValid = startVal >= openingH || startVal <= closingH;
            }
        }

        let isEndValid = true;
        if (endVal) {
            if (openingH <= closingH) {
                isEndValid = endVal >= openingH && endVal <= closingH;
            } else {
                isEndValid = endVal >= openingH || endVal <= closingH;
            }
        }

        if (!isStartValid || !isEndValid) {
            if (timeAlertModal) timeAlertModal.style.display = "block";
            if (startTimeInput) startTimeInput.value = "";
            if (endTimeInput) endTimeInput.value = "";
            return;
        }

        if (formattedDate === dateVal) {
            if (startVal && startVal < currentTime) {
                if (timeAlertModal) timeAlertModal.style.display = "block";
                if (startTimeInput) startTimeInput.value = "";
                if (endTimeInput) endTimeInput.value = "";
                return;
            }
            if (endVal && endVal < currentTime) {
                if (timeAlertModal) timeAlertModal.style.display = "block";
                if (startTimeInput) startTimeInput.value = "";
                if (endTimeInput) endTimeInput.value = "";
                return;
            }
        }

        if (this.isLeadTime && this.reservationLeadTime > 0 && startVal && dateVal) {
            const [sYear, sMonth, sDay] = dateVal.split("-").map(Number);
            const [sHour, sMin] = startVal.split(":").map(Number);
            const bookingStart = new Date(sYear, sMonth - 1, sDay, sHour, sMin, 0);
            const diffInHours = (bookingStart - now) / (1000 * 60 * 60);

            if (diffInHours < this.reservationLeadTime) {
                const hours = Math.floor(this.reservationLeadTime);
                const mins = Math.round((this.reservationLeadTime - hours) * 60);
                let leadTimeStr = "";
                if (hours > 0 && mins > 0) {
                    leadTimeStr = `${hours} hour(s) and ${mins} minute(s)`;
                } else if (hours > 0) {
                    leadTimeStr = `${hours} hour(s)`;
                } else {
                    leadTimeStr = `${mins} minute(s)`;
                }
                if (timeAlertModal) {
                    const title = timeAlertModal.querySelector(".modal-title");
                    if (title) title.textContent = "Lead Time Constraint";
                    const body = timeAlertModal.querySelector(".modal-body p");
                    if (body) body.textContent = `Booking must be made at least ${leadTimeStr} in advance.`;
                    timeAlertModal.style.display = "block";
                }
                if (startTimeInput) startTimeInput.value = "";
                if (endTimeInput) endTimeInput.value = "";
                return;
            }
        }
    }

    onClickCloseAlertBtn() {
        const timeAlertModal = this.el.querySelector("#time_alert_modal");
        if (timeAlertModal) {
            timeAlertModal.style.display = "none";
        }
    }

    onSubmitForm(ev) {
        this.onChangeTime();
        const startTimeInput = this.el.querySelector("#start_time");
        const endTimeInput = this.el.querySelector("#end_time");
        if (!startTimeInput?.value || !endTimeInput?.value) {
            ev.preventDefault();
        }
    }
}

registry.category("public.interactions").add("table_reservation_on_website.reservation", TableReservationBooking);
