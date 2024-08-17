odoo.define('hr_leave_dashboard.TimeOffDashboard', function(require) {
    'use strict';

    var core = require('web.core');
    const config = require('web.config');

    var CalendarRenderer = require("web.CalendarRenderer");
    var CalendarPopover = require("web.CalendarPopover")
    var CalendarController = require("web.CalendarController");
    var CalendarModel = require("web.CalendarModel");
    var viewRegistry = require('web.view_registry');

    var CalendarView = require("web.CalendarView");
    var QWeb = core.qweb;
    var _t = core._t;
    var session = require('web.session');

//    Extending the calendar view to add the details to the dashboard.
    var TimeOffCalendarController = CalendarController.extend({
        events: _.extend({}, CalendarController.prototype.events, {
            'click .btn-time-off': '_onNewTimeOff',
            'click .btn-allocation': '_onNewAllocation',
            'click .print-pdf-report': 'printPdfReport',
        }),

        /**
         * @override
         */
        start: function () {
            this.$el.addClass('o_timeoff_calendar');
            return this._super(...arguments);
        },

        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------

         /**
         * Render the buttons and add new button about
         * time off and allocations request
         *
         * @override
         */

        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            $(QWeb.render('hr_holidays.dashboard.calendar.button', {
                time_off: _t('New Time Off'),
                request: _t('Allocation Request'),
            })).appendTo(this.$buttons);

            if ($node) {
                this.$buttons.appendTo($node);
            } else {
                this.$('.o_calendar_buttons').replaceWith(this.$buttons);
            }
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        _getNewTimeOffContext: function() {
            const { date_from, date_to } = this.model._getTimeOffDates(moment());
            return {
                'default_date_from': date_from,
                'default_date_to': date_to,
                'lang': this.context.lang
            }
        },

        /**
         * Action: create a new time off request
         *
         * @private
         */
        _onNewTimeOff: function () {
            this._rpc({
                model: 'ir.ui.view',
                method: 'get_view_id',
                args: ['hr_holidays.hr_leave_view_form_dashboard_new_time_off'],
            }).then((ids) => {
                this.timeOffDialog = new dialogs.FormViewDialog(this, {
                    res_model: "hr.leave",
                    view_id: ids,
                    context: this._getNewTimeOffContext(),
                    title: _t("New time off"),
                    disable_multiple_selection: true,
                    on_saved: () => {
                        this.reload();
                    },
                });
                this.timeOffDialog.open();
            });
        },

        /**
         * Action: create a new allocation request
         *
         * @private
         */
        _onNewAllocation: function () {
            let self = this;

            self._rpc({
                model: 'ir.ui.view',
                method: 'get_view_id',
                args: ['hr_holidays.hr_leave_allocation_view_form_dashboard'],
            }).then(function(ids) {
                self.allocationDialog = new dialogs.FormViewDialog(self, {
                    res_model: "hr.leave.allocation",
                    view_id: ids,
                    context: {
                        'default_state': 'confirm',
                        'lang': self.context.lang,
                    },
                    title: _t("New Allocation"),
                    disable_multiple_selection: true,
                    on_saved: function() {
                        self.reload();
                    },
                });
                self.allocationDialog.open();
            });
        },
//        Action to print the pdf report of the timeoff.
        printPdfReport: function () {
            const duration = $(this.el.querySelectorAll("#duration")).val();
            var self = this
            this._rpc({
                model: 'hr.leave',
                method: 'get_all_validated_leaves',
                args: [

                ],
            }).then(function(data) {
                var action = {
                    type: "ir.actions.report",
                    report_type: "qweb-pdf",
                    report_name: "hr_leave_dashboard.hr_leave_report",
                    report_file: "hr_leave_dashboard.hr_leave_report",
                    data: {
                        'duration': duration,
                        'all_validated_leaves': data,
                        }
                }
                return self.do_action(action)
                })
        },

        /**
         * @override
         */
        _setEventTitle: function () {
            return _t('Time Off Request');
        },
    });


    var TimeOffCalendarPopover = CalendarPopover.extend({
        template: 'hr_holidays.calendar.popover',

        init: function (parent, eventInfo) {
            this._super.apply(this, arguments);
            const state = this.event.extendedProps.record.state;
            this.canDelete = state && ['validate', 'refuse'].indexOf(state) === -1;
            this.canEdit = state !== undefined;
            this.displayFields = [];

            if (this.modelName === "hr.leave.report.calendar") {
                const duration = this.event.extendedProps.record.display_name.split(':').slice(-1);
                this.display_name = _.str.sprintf(_t("Time Off : %s"), duration);
            } else {
                this.display_name = this.event.extendedProps.record.display_name;
            }
        },
    });

    var TimeOffPopoverRenderer = CalendarRenderer.extend({
        template: "TimeOff.CalendarView.extend",
        /**
         * We're overriding this to display the weeknumbers on the year view
         *
         * @override
         * @private
         */
        _getFullCalendarOptions: function () {
            const oldOptions = this._super(...arguments);
            // Parameters
            oldOptions.views.dayGridYear.weekNumbers = true;
            oldOptions.views.dayGridYear.weekNumbersWithinDays = false;
            return oldOptions;
        },

        config: _.extend({}, CalendarRenderer.prototype.config, {
            CalendarPopover: TimeOffCalendarPopover,
        }),

        _getPopoverParams: function (eventData) {
            let params = this._super.apply(this, arguments);
            let calendarIcon;
            let state = eventData.extendedProps.record.state;

            if (state === 'validate') {
                calendarIcon = 'fa-calendar-check-o';
            } else if (state === 'refuse') {
                calendarIcon = 'fa-calendar-times-o';
            } else if(state) {
                calendarIcon = 'fa-calendar-o';
            }

            params['title'] = eventData.extendedProps.record.display_name.split(':').slice(0, -1).join(':');
            params['template'] = QWeb.render('hr_holidays.calendar.popover.placeholder', {color: this.getColor(eventData.color_index), calendarIcon: calendarIcon});
            return params;
        },

        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self.$el.parent().find('.o_calendar_mini').hide();
            });
        },
        /**
         * @override
         * @private
         */
        _renderCalendar: function() {
            this._super.apply(this, arguments);
            let weekNumbers = this.$el.find('.fc-week-number');
            weekNumbers.each( function() {
                let weekRow = this.parentNode;
                // By default, each month has 6 weeks displayed, hide the week number if there is no days for the week
                if(!weekRow.children[1].classList.length && !weekRow.children[weekRow.children.length-1].classList.length) {
                    this.innerHTML = '';
                }
            });
        },
    });

    var TimeOffCalendarRenderer = TimeOffPopoverRenderer.extend({
        _render: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._rpc({
                    model: 'hr.leave.type',
                    method: 'get_days_all_request',
                    context: self.state.context,
                });
            }).then(function (result) {
                self._rpc({
                model: 'hr.leave',
                method: 'get_current_employee',
                }).then(function (res) {
                self.$el.parent().find('.o_calendar_mini').hide();
                self.$el.parent().find('.o_timeoff_container').remove();
                self._rpc({
                    route: '/hr/get_org_chart',
                    params: {
                        employee_id: res.id,
                        context: session.user_context,
                    },
                    })
                    .then(function (data) {
                        if (result.length > 0) {
                            if (config.device.isMobile) {
                                result.forEach((data) => {
                                    const elem = QWeb.render('hr_holidays.dashboard_calendar_header_mobile', {
                                        timeoff: data,
                                    });
                                    self.$el.find('.o_calendar_filter_item[data-value=' + data[3] + '] .o_cw_filter_title').append(elem);
                                });
                            } else {
                                const elem = QWeb.render('hr_holidays.dashboard_calendar_header', {
                                    timeoffs: result,
                                    employee: res,
                                    employee_org: data,
                                });
                                self.$el.before(elem);
                            }
                        }
                        $('[data-toggle="popover"]').each(function () {
                            $(this).popover({
                                html: true,
                                title: function () {
                                    var $title = $(QWeb.render('hr_orgchart_emp_popover_title', {
                                        employee: {
                                            name: $(this).data('emp-name'),
                                            id: $(this).data('emp-id'),
                                        },
                                    }));
                                    $title.on('click',
                                        '.o_employee_redirect', _.bind(self._onEmployeeRedirect, self));
                                    return $title;
                                },
                                container: this,
                                placement: 'left',
                                trigger: 'focus',
                                content: function () {
                                    var $content = $(QWeb.render('hr_orgchart_emp_popover_content', {
                                        employee: {
                                            id: $(this).data('emp-id'),
                                            name: $(this).data('emp-name'),
                                            direct_sub_count: parseInt($(this).data('emp-dir-subs')),
                                            indirect_sub_count: parseInt($(this).data('emp-ind-subs')),
                                        },
                                    }));
                                    $content.on('click',
                                        '.o_employee_sub_redirect', _.bind(self._onEmployeeSubRedirect, self));
                                    return $content;
                                },
                                template: QWeb.render('hr_orgchart_emp_popover', {}),
                            });
                        });
                    });
                })
            });
        },
//        Function to redirect toi the employee form view.
        _onEmployeeRedirect: function (event) {
            var self = this;
            event.preventDefault();
            var employee_id = parseInt($(event.currentTarget).data('employee-id'));
            return this._rpc({
                model: 'hr.employee',
                method: 'get_formview_action',
                args: [employee_id],
            }).then(function(action) {
                return self.do_action(action);
            });
        },
//        Function to redirect to the sub employee's form view
        _onEmployeeSubRedirect: function (event) {
            event.preventDefault();
            var employee_id = parseInt($(event.currentTarget).data('employee-id'));
            var employee_name = $(event.currentTarget).data('employee-name');
            var type = $(event.currentTarget).data('type') || 'direct';
            var self = this;
            if (employee_id) {
                this._getSubordinatesData(employee_id, type).then(function(data) {
                    var domain = [['id', 'in', data]];
                    return self._rpc({
                        model: 'hr.employee',
                        method: 'get_formview_action',
                        args: [employee_id],
                    }).then(function(action) {
                        action = _.extend(action, {
                            'name': _t('Team'),
                            'view_mode': 'kanban,list,form',
                            'views':  [[false, 'kanban'], [false, 'list'], [false, 'form']],
                            'domain': domain,
                            'context': {
                                'default_parent_id': employee_id,
                            }
                        });
                        delete action['res_id'];
                        return self.do_action(action);
                    });
                });
            }
        },
//        Function to get the details of sub employees.
        _getSubordinatesData: function (employee_id, type) {
            return this._rpc({
                route: '/hr/get_subordinates',
                params: {
                    employee_id: employee_id,
                    subordinates_type: type,
                    context: session.user_context,
                },
            });
        },

    });

    const TimeOffCalendarModel = CalendarModel.extend({
        calendarEventToRecord(event) {
            const res = this._super(...arguments);
            if (['day', 'week'].includes(this.data.scale)) {
                const { date_from, date_to } = this._getTimeOffDates(event.start.clone());

                res['date_from'] = date_from;
                res['date_to'] = date_to;
            }

            return res;
        },

        _getTimeOffDates(date_from) {
            date_from.set({
                'hour': 0,
                'minute': 0,
                'second': 0
            });
            let date_to = date_from.clone().set({
                'hour': 23,
                'minute': 59,
                'second': 59
            });

            date_from.subtract(this.getSession().getTZOffset(date_from), 'minutes');
            date_from = date_from.locale('en').format('YYYY-MM-DD HH:mm:ss');
            date_to.subtract(this.getSession().getTZOffset(date_to), 'minutes');
            date_to = date_to.locale('en').format('YYYY-MM-DD HH:mm:ss');

            return {
                date_from,
                date_to,
            }
        },
    });

    var TimeOffCalendarView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
            Controller: TimeOffCalendarController,
            Renderer: TimeOffCalendarRenderer,
            Model: TimeOffCalendarModel,
        }),
    });

    /**
     * Calendar shown in the "Everyone" menu
     */
    var TimeOffCalendarAllView = CalendarView.extend({
        config: _.extend({}, CalendarView.prototype.config, {
            Controller: TimeOffCalendarController,
            Renderer: TimeOffPopoverRenderer,
            Model: TimeOffCalendarModel,
        }),
    });

    viewRegistry.add('time_off_calendar', TimeOffCalendarView);
    viewRegistry.add('time_off_calendar_all', TimeOffCalendarAllView);
});

