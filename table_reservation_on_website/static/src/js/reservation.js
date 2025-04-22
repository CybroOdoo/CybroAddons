/** @odoo-module **/
import publicWidget from 'web.public.widget';
import { registry } from '@web/core/registry';
import { rpc } from "@web/core/network/rpc_service";
import ajax from "web.ajax";

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
            const result = await ajax.jsonRpc("/pos/get_opening_closing_hours", "call", {});
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
    
    _onChangeDate: function (ev) {
        let selectedDate = new Date(this.$el.find("#date").val());
        const currentDate = new Date();
        if (selectedDate.setHours(0, 0, 0, 0) < currentDate.setHours(0, 0, 0, 0)) {
            this.$el.find("#alert_modal").show();
            this.$el.find("#date").val('');
        }
        this._onChangeTime();
    },
    
    _onClickCloseBtn: function() {
        this.$el.find("#alert_modal").hide();
    },
    
    _onChangeTime: function() {
        let start_time = this.$el.find("#start_time");
        let end_time = this.$el.find("#end_time");

        let now = new Date();
        let currentHours = now.getHours().toString().padStart(2, '0');
        let currentMinutes = now.getMinutes().toString().padStart(2, '0');
        let currentTime = `${currentHours}:${currentMinutes}`;

        const currentDate = new Date();
        const formattedDate = currentDate.toISOString().split('T')[0];

        if (start_time.val() && end_time.val()) {
            if (start_time.val() > end_time.val() || start_time.val() == end_time.val()) {
                this.$el.find("#time_alert_modal").show();
                start_time.val('');
                end_time.val('');
                return;
            }
        }

        if (!this.openingHour || !this.closingHour) {
            console.warn("Opening and closing hours are not set.");
            return;
        }

        if (start_time.val() && (start_time.val() < this.openingHour || start_time.val() > this.closingHour)) {
            this.$el.find("#time_alert_modal").show();
            start_time.val('');
            end_time.val('');
            return;
        }

        if (end_time.val() && (end_time.val() < this.openingHour || end_time.val() > this.closingHour)) {
            this.$el.find("#time_alert_modal").show();
            start_time.val('');
            end_time.val('');
            return;
        }

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

    _onClickCloseAlertBtn: function() {
        this.$el.find("#time_alert_modal").hide();
    }
});