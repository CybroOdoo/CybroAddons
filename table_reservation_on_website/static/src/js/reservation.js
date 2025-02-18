/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.reservation = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'change #date': '_onChangeDate',
        'change #start_time': '_onChangeTime',
        'change #end_time': '_onChangeTime',
        'click .close_btn_alert_modal': '_onClickCloseBtn',
        'click .close_btn_time_alert_modal': '_onClickCloseAlertBtn',
    },
    async start() {
        this.openingHour = null;
        this.closingHour = null;
        await this._fetchOpeningClosingHours();
    },
    async _fetchOpeningClosingHours() {
        try {
            const result = await jsonrpc('/pos/get_opening_closing_hours', {});
            if (result && !result.error) {
                this.openingHour = result.opening_hour;
                this.closingHour = result.closing_hour;
            } else {
                console.error("Error: ", result.error);
            }
        } catch (error) {
            console.error("Failed to fetch opening and closing hours:", error);
        }
    },
    // To ensure booking date is a valid one.
    _onChangeDate: function (ev) {
        var selectedDate = new Date(this.$el.find("#date").val())
        const currentDate = new Date();
        if (selectedDate.setHours(0, 0, 0, 0) < currentDate.setHours(0, 0, 0, 0)) {
            this.$el.find("#alert_modal").show();
            this.$el.find("#date").val('')
        }
        this._onChangeTime()
    },
    // To close the alert modal if invalid date is chosen.
    _onClickCloseBtn: function() {
        this.$el.find("#alert_modal").hide();
    },
    // Display a modal if invalid start time and end is chosen.
    _onChangeTime: function() {
    var start_time = this.$el.find("#start_time");
    var end_time = this.$el.find("#end_time");

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
        if (start_time.val() > end_time.val()) {
            this.$el.find("#time_alert_modal").show();
            start_time.val('');
            end_time.val('');
            return;
        }
        if (start_time.val() == end_time.val()) {
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
    if (start_time.val() && (start_time.val() < this.openingHour || start_time.val() > this.closingHour)) {
        this.$el.find("#time_alert_modal").show();
        start_time.val('');
        end_time.val('');
        return;
    }

    if (end_time.val() && (end_time.val() < this.openingHour || end_time.val() > this.closingHour)) {
        var e = this.$el.find("#time_alert_modal").show();
        start_time.val('');
        end_time.val('');
        return;
    }

    // Ensure the time is not in the past for the current day
    if (formattedDate == this.$el.find("#date").val()) {
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
},

    // To close the alert modal if invalid booking start and end time is chosen.
    _onClickCloseAlertBtn: function() {
        this.$el.find("#time_alert_modal").hide()
    }
});
