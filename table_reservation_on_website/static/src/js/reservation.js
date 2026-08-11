/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.reservation = publicWidget.Widget.extend({
    selector: '#table_reservation_page',
    events: {
        'change #date': '_onChangeDate',
        'change #start_time': '_onChangeTime',
        'blur #start_time': '_onChangeTime',
        'change #end_time': '_onChangeTime',
        'blur #end_time': '_onChangeTime',
        'submit form': '_onSubmitForm',
        'click .close_btn_alert_modal': '_onClickCloseBtn',
        'click .close_btn_time_alert_modal': '_onClickCloseAlertBtn',
    },
    async start() {
        this.openingHour = null;
        this.closingHour = null;
        this.isLeadTime = false;
        this.reservationLeadTime = 0.0;
        await this._fetchOpeningClosingHours();
    },
    async _fetchOpeningClosingHours() {
        try {
            const result = await rpc('/pos/get_opening_closing_hours', {});
            if (result && !result.error) {
                this.openingHour = result.opening_hour;
                this.closingHour = result.closing_hour;
                this.isLeadTime = result.is_lead_time;
                this.reservationLeadTime = result.reservation_lead_time || 0.0;
            } else {
                console.error("Error: ", result.error);
            }
        } catch (error) {
            console.error("Failed to fetch opening and closing hours:", error);
        }
    },
    // To ensure booking date is a valid one.
    _onChangeDate: function (ev) {
        var dateVal = this.$el.find("#date").val();
        if (!dateVal) {
            return;
        }
        var selectedDate = new Date(dateVal);
        if (isNaN(selectedDate.getTime())) {
            return;
        }
        if (selectedDate.getFullYear() < 1000) {
            return;
        }
        if (selectedDate.getFullYear() > 9999) {
            this.$el.find("#alert_modal .modal-title").text("Invalid Date");
            this.$el.find("#alert_modal .modal-body p").text("Invalid Year");
            this.$el.find("#alert_modal").show();
            this.$el.find("#date").val('');
            return;
        }
        const currentDate = new Date();
        if (selectedDate.setHours(0, 0, 0, 0) < currentDate.setHours(0, 0, 0, 0)) {
            this.$el.find("#alert_modal").show();
            this.$el.find("#date").val('')
        }
        this._onChangeTime()
    },
    // To close the alert modal if invalid date is chosen.
    _onClickCloseBtn: function () {
        this.$el.find("#alert_modal").hide();
    },
    // Display a modal if invalid start time and end is chosen.
    _onChangeTime: function () {
        var start_time = this.$el.find("#start_time");
        var end_time = this.$el.find("#end_time");
        var date_val = this.$el.find("#date").val();

        // Reset default modal message
        this.$el.find("#time_alert_modal .modal-title").text("Invalid Time");
        this.$el.find("#time_alert_modal .modal-body p").text("Please select a valid booking start and end time.");

        let now = new Date();
        let currentHours = now.getHours().toString().padStart(2, '0');
        let currentMinutes = now.getMinutes().toString().padStart(2, '0');
        let currentTime = `${currentHours}:${currentMinutes}`;

        const currentDate = new Date();
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0');
        const day = String(currentDate.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;

        if (start_time.val() && end_time.val()) {
            const timeToMinutes = (timeStr) => {
                if (!timeStr) return 0;
                const [hours, minutes] = timeStr.split(':').map(Number);
                return hours * 60 + minutes;
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

            const startLinear = getLinearMinutes(start_time.val());
            const endLinear = getLinearMinutes(end_time.val());

            if (startLinear >= endLinear) {
                this.$el.find("#time_alert_modal").show();
                start_time.val('');
                end_time.val('');
                return;
            }
        }

        // Ensure opening and closing hours are available
        if (!this.openingHour || !this.closingHour) {
            console.warn("Opening and closing hours are not set.");
            return;
        }

        // Validate start and end time against opening and closing time
        const openingH = this.openingHour;
        const closingH = this.closingHour;
        const startV = start_time.val();
        const endV = end_time.val();

        let isStartValid = true;
        if (startV) {
            if (openingH <= closingH) {
                isStartValid = startV >= openingH && startV <= closingH;
            } else {
                isStartValid = startV >= openingH || startV <= closingH;
            }
        }

        let isEndValid = true;
        if (endV) {
            if (openingH <= closingH) {
                isEndValid = endV >= openingH && endV <= closingH;
            } else {
                isEndValid = endV >= openingH || endV <= closingH;
            }
        }
        if (!isStartValid || !isEndValid) {
            this.$el.find("#time_alert_modal").show();
            start_time.val('');
            end_time.val('');
            return;
        }

        // Ensure the time is not in the past for the current day
        if (formattedDate == date_val) {
            if (start_time.val() && start_time.val() < currentTime) {
                this.$el.find("#time_alert_modal").show();
                start_time.val('');
                end_time.val('');
                return;
            }
            if (end_time.val() && end_time.val() < currentTime) {
                this.$el.find("#time_alert_modal").show();
                start_time.val('');
                end_time.val('');
                return;
            }
        }

        // Validate Lead Time constraint
        if (this.isLeadTime && this.reservationLeadTime > 0 && start_time.val() && date_val) {
            const [sYear, sMonth, sDay] = date_val.split('-').map(Number);
            const [sHour, sMin] = start_time.val().split(':').map(Number);
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
                this.$el.find("#time_alert_modal .modal-title").text("Lead Time Constraint");
                this.$el.find("#time_alert_modal .modal-body p").text(`Booking must be made at least ${leadTimeStr} in advance.`);
                this.$el.find("#time_alert_modal").show();
                start_time.val('');
                end_time.val('');
                return;
            }
        }
    },

    // To close the alert modal if invalid booking start and end time is chosen.
    _onClickCloseAlertBtn: function () {
        this.$el.find("#time_alert_modal").hide()
    },
    _onSubmitForm: function (ev) {
        this._onChangeTime();
        var start_time = this.$el.find("#start_time").val();
        var end_time = this.$el.find("#end_time").val();
        if (!start_time || !end_time) {
            ev.preventDefault();
        }
    }
});
