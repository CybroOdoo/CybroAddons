odoo.define('project_task_timer.timer', function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var fieldUtils = require('web.field_utils');
    var _t = core._t;
    var TimeCounter = AbstractField.extend({
        start: function () {
            this._super.apply(this, arguments);
            this.duration = 0; // Initialize duration
            this._startTimeCounter();
        },
        destroy: function () {
            this._super.apply(this, arguments);
            clearTimeout(this.timer);
        },
        _render: function () {
            this.$el.addClass('o_timer');
            this.$el.text(this._formatDuration(this.duration));
        },
        _startTimeCounter: function () {
            var self = this;
            clearTimeout(this.timer);

            this.timer = setTimeout(function () {
                self.duration += 1000;
                self._render();
                self._startTimeCounter();
            }, 1000);
        },
        _formatDuration: function (duration) {
            var hours = Math.floor(duration / (60 * 60 * 1000));
            var minutes = Math.floor((duration % (60 * 60 * 1000)) / (60 * 1000));
            var seconds = Math.floor((duration % (60 * 1000)) / 1000);
            // Ensure two-digit formatting for minutes and seconds
            var formatted = (hours < 10 ? '0' : '') + hours + ':' +
                            (minutes < 10 ? '0' : '') + minutes + ':' +
                            (seconds < 10 ? '0' : '') + seconds;
            return formatted;
        },
    });
    field_registry.add('timesheet_timer', TimeCounter);
    return TimeCounter;
});
