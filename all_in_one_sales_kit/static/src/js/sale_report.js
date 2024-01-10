odoo.define('all_in_one_sales_kit.sale_report', function(require) {
	'use strict';
	var AbstractAction = require('web.AbstractAction');
	var core = require('web.core');
	var rpc = require('web.rpc');
	var QWeb = core.qweb;
	var _t = core._t;
	var time = require('web.time');
    var framework = require('web.framework');
    var session = require('web.session');
    /**
     * SaleReport class for handling sales report actions.
     * Extends AbstractAction.
     *
     * @property {string} template - The template associated with this action.
     * @property {Object} events - Event handlers for various HTML elements.
     * @property {Array} report_lines - Array of report lines.
     * @property {number|null} wizard_id - ID of the associated wizard or null if not available.
     */
	var SaleReport = AbstractAction.extend({
		template: 'SaleReport',
		events: {
			'click #apply_filter': 'apply_filter',
			'click #pdf': 'print_pdf',
			'click #xlsx': 'print_xlsx',
			'click .view_sale_order': 'button_view_order',
			'mousedown div.input-group.date[data-target-input="nearest"]': '_onCalendarIconClick',
		},
		 /**
         * Constructor for the SaleReport class.
         *
         * @param {Object} parent - The parent object.
         * @param {Object} action - The action object.
         */
		init: function(parent, action) {
			this._super(parent, action);
			this.report_lines = action.report_lines;
			this.wizard_id = action.context.wizard | null;
		},
		 /**
         * Method called when the object is started or initialized.
         * Sets up the initial state, creates a sales report, and loads data.
         */
		start: function() {
			var self = this;
			self.initial_render = true;
			rpc.query({
				model: 'sales.report',
				method: 'create',
				args: [{
				}]
			}).then(function(res) {
				self.wizard_id = res;
				self.load_data(self.initial_render);
                self.apply_filter();
			})
		},
		_onCalendarIconClick: function(ev) {
		/*It is to get selected date.*/
			var $calendarInputGroup = $(ev.currentTarget);
			var calendarOptions = {
				minDate: moment({
					y: 1000
				}),
				maxDate: moment().add(200, 'y'),
				calendarWeeks: true,
				defaultDate: moment().format(),
				sideBySide: true,
				buttons: {
					showClear: true,
					showClose: true,
					showToday: true,
				},
				icons: {
					date: 'fa fa-calendar',
				},
				locale: moment.locale(),
				format: time.getLangDateFormat(),
				widgetParent: 'body',
				allowInputToggle: true,
			};
			$calendarInputGroup.datetimepicker(calendarOptions);
		},
		/**
         * Loads data for the sales report, including filters and order details.
         *
         * @param {boolean} initial_render - Flag indicating whether it's the initial rendering.
         */
		load_data: function(initial_render = true) {
			var self = this;
			self._rpc({
				model: 'sales.report',
				method: 'sale_report',
				args: [
					[this.wizard_id]
				],
			}).then(function(datas) {
				if (initial_render) {
					self.$('.filter_view_sr').html(QWeb.render('saleFilterView', {
						filter_data: datas['filters'],
					}));
					self.$el.find('.report_type').select2({
						placeholder: ' Report Type...',
					});
				}
				if (datas['orders'])
					self.$('.table_view_sr').html(QWeb.render('SaleOrderTable', {
						filter: datas['filters'],
						order: datas['orders'],
						report_lines: datas['report_lines'],
						main_lines: datas['report_main_line']
					}));
			})
		},
		print_pdf: function(e) {
		/*This is to pass data need to print in pdf report*/
			e.preventDefault();
			var self = this;
			var action_title = self._title;
			self._rpc({
				model: 'sales.report',
				method: 'sale_report',
				args: [
					[self.wizard_id]
				],
			}).then(function(data) {
				var action = {
					'type': 'ir.actions.report',
					'report_type': 'qweb-pdf',
					'report_name': 'all_in_one_sales_kit.sale_order_report',
					'report_file': 'all_in_one_sales_kit.sale_order_report',
					'data': {
						'report_data': data
					},
					'context': {
						'active_model': 'sales.report',
						'landscape': 1,
						'sale_order_report': true

					},
					'display_name': 'Sale Order',
				};
				return self.do_action(action);
			});
		},
		print_xlsx: function() {
		/*This is to pass data need to print in xlsx report*/
			var self = this;
			self._rpc({
				model: 'sales.report',
				method: 'sale_report',
				args: [
					[self.wizard_id]
				],
			}).then(function(data) {
				var action = {
					'data': {
						'model': 'sales.report',
						'options': JSON.stringify(data),
						'output_format': 'xlsx',
						'report_name': 'Sale Report',
					},
				};
                  self.downloadXlsx(action);
			});
		},
        downloadXlsx: function (action){
        /*It is to pass data needed to print xlsx report*/
        framework.blockUI();
            session.get_file({
                url: '/xlsx_reports',
                data: action.data,
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
        },
		button_view_order: function(event) {
		/*It is to show the corresponding order on button click*/
			event.preventDefault();
			var self = this;
			var context = {};
			this.do_action({
				name: _t("Sale Order"),
				type: 'ir.actions.act_window',
				res_model: 'sale.order',
				view_type: 'form',
				domain: [
					['id', '=', $(event.target).closest('.view_sale_order').attr('id')]
				],
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			});
		},
		apply_filter: function() {
		/*It is to get data according to the filters applied*/
			var self = this;
			self.initial_render = false;
			var filter_data_selected = {};
			if (this.$el.find('.datetimepicker-input[name="date_from"]').val()) {
				filter_data_selected.date_from = moment(this.$el.find('.datetimepicker-input[name="date_from"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
			}
			if (this.$el.find('.datetimepicker-input[name="date_to"]').val()) {
				filter_data_selected.date_to = moment(this.$el.find('.datetimepicker-input[name="date_to"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
			}
			if ($(".report_type").length) {
				var report_res = document.getElementById("report_res")
				filter_data_selected.report_type = $(".report_type")[1].value
				report_res.value = $(".report_type")[1].value
				report_res.innerHTML = report_res.value;
				if ($(".report_type")[1].value == "") {
					report_res.innerHTML = "report_by_order";
				}
			}
			rpc.query({
				model: 'sales.report',
				method: 'write',
				args: [
					self.wizard_id, filter_data_selected
				],
			}).then(function(res) {
				self.initial_render = false;
				self.load_data(self.initial_render);
			});
		},
	});
	core.action_registry.add("s_r", SaleReport);
	return SaleReport;
});
