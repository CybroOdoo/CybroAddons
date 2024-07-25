/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.reservation = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'change #date': '_onChangeDate',
        'change #start_time': '_onChangeTime',
        'change #end_time': '_onChangeTime',
        'click .close_btn_alert_modal': '_onClickCloseBtn',
        'click .close_btn_time_alert_modal': '_onClickCloseAlertBtn',
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
        var start_time = this.$el.find("#start_time")
        var end_time = this.$el.find("#end_time")
        let now = new Date();
        // Get the current time
        let currentHours = now.getHours().toString().padStart(2, '0');
        let currentMinutes = now.getMinutes().toString().padStart(2, '0');
        let currentTime = `${currentHours}:${currentMinutes}`;
        // Get the current date
        const currentDate = new Date();
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0'); // Months are zero-based
        const day = String(currentDate.getDate()).padStart(2, '0');
        // Format the date as YYYY-MM-DD
        const formattedDate = `${year}-${month}-${day}`;
        if (start_time.val() && end_time.val()) {
            if (start_time.val() > end_time.val()) {
                this.$el.find("#time_alert_modal").show()
                start_time.val('')
                end_time.val('')
            }
        }
        if (start_time.val() && end_time.val() && (start_time.val() == end_time.val())) {
            this.$el.find("#time_alert_modal").show()
            start_time.val('')
            end_time.val('')
        }
        if (formattedDate == this.$el.find("#date").val()){
            if (start_time.val() && start_time.val() < currentTime) {
                this.$el.find("#time_alert_modal").show()
                start_time.val('')
                end_time.val('')
            }
            if (end_time.val() && end_time.val() < currentTime) {
                this.$el.find("#time_alert_modal").show()
                start_time.val('')
                end_time.val('')
            }
        }
    },
    // To close the alert modal if invalid booking start and end time is chosen.
    _onClickCloseAlertBtn: function() {
        this.$el.find("#time_alert_modal").hide()
    }
});
