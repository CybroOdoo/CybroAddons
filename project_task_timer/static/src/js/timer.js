odoo.define('timer_widget.timer', function (require) {
"use strict";

var core = require('web.core');
var common = require('web.form_common');
var Model = require('web.Model');
var time = require('web.time');
var utils = require('web.utils');

var _t = core._t;

var TimeCounter = common.AbstractField.extend(common.ReinitializeFieldMixin, {
    start: function() {
        this._super();
        var self = this;
        this.field_manager.on("view_content_has_changed", this, function () {
            self.render_value();
        });
    },
    start_time_counter: function(){
        var self = this;
        clearTimeout(this.timer);
        if (this.field_manager.datarecord.is_user_working) {
            this.duration += 1000;
            this.timer = setTimeout(function() {
                self.start_time_counter();
            }, 1000);
        } else {
            clearTimeout(this.timer);
        }
        this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
    },
    render_value: function() {
        this._super.apply(this, arguments);
        var self = this;
        this.duration;
        var productivity_domain = [['task_id', '=', this.field_manager.datarecord.id], ['user_id', '=', self.session.uid]];
        new Model('account.analytic.line').call('search_read', [productivity_domain, []]).then(function(result) {
            if (self.get("effective_readonly")) {
                self.$el.removeClass('o_form_field_empty');
                var current_date = new Date();
                self.duration = 0;
                _.each(result, function(data) {
                    self.duration += data.date_end ? self.get_date_difference(data.date_start, data.date_end) : self.get_date_difference(time.auto_str_to_date(data.date_start), current_date);
                });
                self.start_time_counter();
            }
        });
    },
    get_date_difference: function(date_start, date_deadline) {
        var difference = moment(date_deadline).diff(moment(date_start));
        return moment.duration(difference);
    },
});

core.form_widget_registry.add('time_counter', TimeCounter);
});
