odoo.define('purchase_report_generator.purchase_report', function(require) {
	'use strict';
	var AbstractAction = require('web.AbstractAction');
	var core = require('web.core');
	var rpc = require('web.rpc');
	var QWeb = core.qweb;
	var _t = core._t;
	var datepicker = require('web.datepicker');
	var time = require('web.time');

    var framework = require('web.framework');
    var session = require('web.session');

	var PurchaseReport = AbstractAction.extend({
		template: 'PurchaseReport',
		events: {
			'click #apply_filter': 'apply_filter',
			'click #pdf': 'print_pdf',
			'click #xlsx': 'print_xlsx',
			'click .view_purchase_order': 'button_view_order',
			'mousedown div.input-group.date[data-target-input="nearest"]': '_onCalendarIconClick',


		},


		init: function(parent, action) {
			this._super(parent, action);
			this.report_lines = action.report_lines;
			this.wizard_id = action.context.wizard | null;

		},
		start: function() {
			var self = this;
			self.initial_render = true;
			console.log("kooooooooooo")
			rpc.query({
				model: 'dynamic.purchase.report',
				method: 'create',
				args: [{
				}]
			}).then(function(res) {
			console.log(res,"ghkddddddddddddddddddddddddddddddddd")
				self.wizard_id = res;
				self.load_data(self.initial_render);
//                self.apply_filter();
			})
		},

		_onCalendarIconClick: function(ev) {
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


		load_data: function(initial_render = true) {
			var self = this;
			self._rpc({
				model: 'dynamic.purchase.report',
				method: 'purchase_report',
				args: [
					[this.wizard_id]
				],
			}).then(function(datas) {
				if (initial_render) {
					self.$('.filter_view_pr').html(QWeb.render('PurchaseFilterView', {
						filter_data: datas['filters'],

					}));
					self.$el.find('.report_type').select2({
						placeholder: ' Report Type...',
					});

				}

				if (datas['orders'])
					self.$('.table_view_pr').html(QWeb.render('PurchaseOrderTable', {
						filter: datas['filters'],
						order: datas['orders'],
						report_lines: datas['report_lines'],
						main_lines: datas['report_main_line']

					}));
			})
		},

		print_pdf: function(e) {
			e.preventDefault();
			var self = this;
			var action_title = self._title;
			self._rpc({
				model: 'dynamic.purchase.report',
				method: 'purchase_report',
				args: [
					[self.wizard_id]
				],
			}).then(function(data) {
				var action = {
					'type': 'ir.actions.report',
					'report_type': 'qweb-pdf',
					'report_name': 'purchase_report_generator.purchase_order_report',
					'report_file': 'purchase_report_generator.purchase_order_report',
					'data': {
						'report_data': data
					},
					'context': {
						'active_model': 'purchase.report',
						'landscape': 1,
						'purchase_order_report': true

					},
					'display_name': 'Purchase Order',
				};
				return self.do_action(action);
			});

		},
		print_xlsx: function() {
			var self = this;
			self._rpc({
				model: 'dynamic.purchase.report',
				method: 'purchase_report',
				args: [
					[self.wizard_id]
				],
			}).then(function(data) {

				var action = {
					'data': {
						'model': 'dynamic.purchase.report',
						'options': JSON.stringify(data['orders']),
						'output_format': 'xlsx',
						'report_data': JSON.stringify(data['report_lines']),
						'report_name': 'Purchase Report',
						'dfr_data': JSON.stringify(data),
					},
				};
                  self.downloadXlsx(action);

			});
		},

        downloadXlsx: function (action){
        framework.blockUI();
            session.get_file({
                url: '/purchase_dynamic_xlsx_reports',
                data: action.data,
                complete: framework.unblockUI,
                error: (error) => this.call('crash_manager', 'rpc_error', error),
            });
        },

		button_view_order: function(event) {
			event.preventDefault();
			var self = this;
			var context = {};
			this.do_action({
				name: _t("Purchase Order"),
				type: 'ir.actions.act_window',
				res_model: 'purchase.order',
				view_type: 'form',
				domain: [
					['id', '=', $(event.target).closest('.view_purchase_order').attr('id')]
				],
				views: [
					[false, 'list'],
					[false, 'form']
				],
				target: 'current'
			});
		},
		//
		apply_filter: function() {
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
				model: 'dynamic.purchase.report',
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
	core.action_registry.add("pu_r", PurchaseReport);
	return PurchaseReport;
});