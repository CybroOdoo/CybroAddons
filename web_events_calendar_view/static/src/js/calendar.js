odoo.define('web_events_calendar_view.calendar', function (require) {
    "use strict";
    var animation = require('website.content.snippets.animation');
    var core = require("web.core");
    var time = require("web.time");
    var ajax = require("web.ajax");
    var DATE_FORMAT = time.strftime_to_moment_format("%Y-%m-%d");
    var DATETIME_FORMAT = time.strftime_to_moment_format(
        "%Y-%m-%d %H:%M:%S");
    var INVERSE_FORMAT = "L";

    var CustomCalendar = animation.Class.extend({
        selector: ".s_event_calendar_list",
        init: function () {
            this.datepickerOptions = {
                inline: true,
                minDate: moment().subtract(100, "years"),
                maxDate: moment().add(100, "years"),
                icons: {
                    previous: "fa fa-chevron-left",
                    next: "fa fa-chevron-right",
                },
                format: DATE_FORMAT,
                useCurrent: false,
                locale: moment.locale(),
            };
            return this._super.apply(this, arguments);
        },

        start: function (editableMode) {
            this._super.apply(this, arguments);

            if (editableMode) {
                return;
            }
            this.selectedDates = {
                min: null,
                max: null,
                matches: [],
            };

            this.$calendar = this.$target.find('.s_event_calendar')
                .on("change.datetimepicker", $.proxy(this, "dateSelected"))
                .on("update.datetimepicker", $.proxy(this, "calendarMoved"));
            this.$list = this.$target.find(".s_event_list");
            this.defaultAmount = Number(this.$(".js_amount").html()) || 4;
            this.dateFormat = this.$list.data("dateFormat") || "LLL";
            // Get initial events to render the list
            this.loadEvents(null, this.defaultAmount)
                .then($.proxy(this, "renderList"));
            // Preload dates and render the calendar
            this.preloadDates(moment())
                .then($.proxy(this, "renderCalendar"));
        },

        dateSelected: function (event) {
            this.loadEvents(event.date.format(DATE_FORMAT))
                .then($.proxy(this, "renderList"));
        },

        calendarMoved: function (event) {
            if (event.change !== "M") {
                // We only care when months are displayed
                return;
            }
            // Preload dates if needed and show evented days
            this.preloadDates(event.viewDate);
        },

        preloadDates: function (when) {
            var margin = moment.duration(4, "months");
            // Don't preload if we have up to 4 months of margin
            if (
                this.selectedDates.min && this.selectedDates.max &&
                this.selectedDates.min <= when - margin &&
                this.selectedDates.max >= when + margin
            ) {
                return $.Deferred().resolve();
            }
            // Default values
            margin.add(2, "months");
            var start = moment(when - margin),
                end = moment(when + margin);
            // If we already preloaded, preload 6 more months
            if (this.selectedDates.min) {
                start.subtract(6, "months");
            }
            if (this.selectedDates.max) {
                end.add(6, "months");
            }
            // Do the preloading
            return this.loadDates(start, end);
        },

        loadDates: function (start, end) {
            return ajax.rpc(
                "/web_events_calendar_view/days_with_events",
                {
                    start: start.format(DATE_FORMAT),
                    end: end.format(DATE_FORMAT),
                }
            ).then($.proxy(this, "updateDatesCache", start, end));
        },

        updateDatesCache: function (start, end, dates) {
            if (!this.selectedDates.min || this.selectedDates.min > start) {
                this.selectedDates.min = start;
            }
            if (!this.selectedDates.max || this.selectedDates.max < end) {
                this.selectedDates.max = end;
            }
            this.selectedDates.matches = _.union(this.selectedDates.matches, dates);
        },

        loadEvents: function (day, limit) {
            return ajax.rpc(
                "/web_events_calendar_view/events_for_day",
                {day: day, limit: limit}
            );
        },

        renderCalendar: function () {
            var enabledDates = _.map(this.selectedDates.matches, function (ndate) {
                return moment(ndate, DATE_FORMAT);
            });
            this.$calendar.empty().datetimepicker(_.extend({},
                this.datepickerOptions, {'enabledDates': enabledDates}));
        },

        renderList: function (events) {
            this.$list.html(core.qweb.render(
                "web_events_calendar_view.list",
                {events: events}
            ));
        },
    });

    animation.registry.web_events_calendar_view = CustomCalendar;

    return {
        CustomCalendar: CustomCalendar,
        DATE_FORMAT: DATE_FORMAT,
        DATETIME_FORMAT: DATETIME_FORMAT,
        INVERSE_FORMAT: INVERSE_FORMAT,
    };
});
