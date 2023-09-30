odoo.define('dynamic_accounts_report.general_ledger', function(require) {
	'use strict';
	var AbstractAction = require('web.AbstractAction');
	var core = require('web.core');
	var field_utils = require('web.field_utils');
	var rpc = require('web.rpc');
	var session = require('web.session');
	var utils = require('web.utils');
	var QWeb = core.qweb;
	var _t = core._t;
	var trial = require('dynamic_accounts_report.trial_balance');
	var framework = require('web.framework');

	var datepicker = require('web.datepicker');
	var time = require('web.time');
	window.click_num = 0;
	var GeneralLedger = AbstractAction.extend({
		template: 'GeneralTemp',
		events: {
			'click .parent-line': 'journal_line_click',
			'click .child_col1': 'journal_line_click',
			'click #apply_filter': 'apply_filter',
			'click #pdf': 'print_pdf',
			'click #xlsx': 'print_xlsx',
			'click .gl-line': 'show_drop_down',
			'click .view-account-move': 'view_acc_move',
			'mousedown div.input-group.date[data-target-input="nearest"]': '_onCalendarIconClick',
		},
		init: function(parent, action) {
			this._super(parent, action);
			this.currency = action.currency;
			this.report_lines = action.report_lines;
			this.wizard_id = action.context.wizard | null;
		},
		start: function() {
			var self = this;
			self.initial_render = true;
			if (this.searchModel.config.domain.length != 0) {
				rpc.query({
					model: 'account.general.ledger',
					method: 'create',
					args: [{
						account_ids: [this.searchModel.config.domain[0][2]]
					}]
				}).then(function(t_res) {
					self.wizard_id = t_res;
					self.load_data(self.initial_render);
				})
			} else {
				rpc.query({
					model: 'account.general.ledger',
					method: 'create',
					args: [{}]
				}).then(function(t_res) {
					self.wizard_id = t_res;
					self.load_data(self.initial_render);
				})
			}
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
			self.$(".categ").empty();
			try {
				var self = this;
				var action_title = self._title
				self._rpc({
					model: 'account.general.ledger',
					method: 'view_report',
					args: [
						[this.wizard_id], action_title
					],
				}).then(function(datas) {
					//                    _.each(datas['report_lines'], function(rep_lines) {
					//                            rep_lines.debit = self.format_currency(datas['currency'],rep_lines.debit);
					//                            rep_lines.credit = self.format_currency(datas['currency'],rep_lines.credit);
					//                            rep_lines.balance = self.format_currency(datas['currency'],rep_lines.balance);
					//                            });

					if (initial_render) {
						self.$('.filter_view_tb').html(QWeb.render('GLFilterView', {
							filter_data: datas['filters'],
							title: datas['name'],
							//                                        eng_title : datas['eng_title'],
						}));
						self.$el.find('.journals').select2({
							placeholder: ' Journals...',
						});
						self.$el.find('.account-partner').select2({
							placeholder: ' Accounts...',
						});
						self.$el.find('.account-tag').select2({
							placeholder: ' Account Tag...',
						});
						self.$el.find('.analytics').select2({
							placeholder: 'Analytic Accounts...',
						});
						self.$el.find('.target_move').select2({
							placeholder: 'Target Move...',
						});
					}
					var child = [];
					self.$('.table_view_tb').html(QWeb.render('GLTable', {
						report_lines: datas['report_lines'],
						filter: datas['filters'],
						currency: datas['currency'],
						credit_total: datas['credit_total'],
						debit_total: datas['debit_total'],
						debit_balance: datas['debit_balance']
					}));
				});
			} catch (el) {
				window.location.href
			}
		},

		print_pdf: function(e) {
			e.preventDefault();
			var self = this;
			var action_title = self._title
			self._rpc({
				model: 'account.general.ledger',
				method: 'view_report',
				args: [
					[self.wizard_id], action_title
				],
			}).then(function(data) {
				var action = {
					'type': 'ir.actions.report',
					'report_type': 'qweb-pdf',
					'report_name': 'dynamic_accounts_report.general_ledger',
					'report_file': 'dynamic_accounts_report.general_ledger',
					'data': {
						'report_data': data
					},
					'context': {
						'active_model': 'account.general.ledger',
						'landscape': 1,
						'trial_pdf_report': true
					},
					'display_name': action_title,
				};
				return self.do_action(action);
			});
		},

		print_xlsx: function() {
			var self = this;
			var action_title = self._title
			self._rpc({
				model: 'account.general.ledger',
				method: 'view_report',
				args: [
					[self.wizard_id], action_title
				],
			}).then(function(data) {
				var action = {
					//                    'type': 'ir_actions_dynamic_xlsx_download',
					'data': {
						'model': 'account.general.ledger',
						'options': JSON.stringify(data['filters']),
						'output_format': 'xlsx',
						'report_data': JSON.stringify(data['report_lines']),
						'report_name': action_title,
						'dfr_data': JSON.stringify(data),
					},
				};
				//                return self.do_action(action);
				self.downloadXlsx(action)
			});
		},

		downloadXlsx: function(action) {
			framework.blockUI();
			session.get_file({
				url: '/dynamic_xlsx_reports',
				data: action.data,
				complete: framework.unblockUI,
				error: (error) => this.call('crash_manager', 'rpc_error', error),
			});
		},

		create_lines_with_style: function(rec, attr, datas) {
			var temp_str = "";
			var style_name = "border-bottom: 1px solid #e6e6e6;";
			var attr_name = attr + " style=" + style_name;

			temp_str += "<td  class='child_col1' " + attr_name + " >" + rec['code'] + rec['name'] + "</td>";
			if (datas.currency[1] == 'after') {
				temp_str += "<td  class='child_col2' " + attr_name + " >" + rec['debit'].toFixed(2) + datas.currency[0] + "</td>";
				temp_str += "<td  class='child_col3' " + attr_name + " >" + rec['credit'].toFixed(2) + datas.currency[0] + "</td>";
			} else {
				temp_str += "<td  class='child_col2' " + attr_name + " >" + datas.currency[0] + rec['debit'].toFixed(2) + "</td>";
				temp_str += "<td  class='child_col3' " + attr_name + ">" + datas.currency[0] + rec['credit'].toFixed(2) + "</td>";

			}
			return temp_str;
		},

		journal_line_click: function(el) {
			click_num++;
			var self = this;
			var line = $(el.target).parent().data('id');
			return self.do_action({
				type: 'ir.actions.act_window',
				view_type: 'form',
				view_mode: 'form',
				res_model: 'account.move',
				views: [
					[false, 'form']
				],
				res_id: line,
				target: 'current',
			});

		},

		format_currency: function(currency, amount) {
			if (typeof(amount) != 'number') {
				amount = parseFloat(amount);
			}
			var formatted_value = (parseInt(amount)).toLocaleString(currency[2], {
				minimumFractionDigits: 2
			})
			return formatted_value
		},

		show_drop_down: function(event) {
			event.preventDefault();
			var self = this;
			var account_id = $(event.currentTarget).data('account-id');
			var offset = 0;
			var td = $(event.currentTarget).next('tr').find('td');
			if (td.length == 1) {
				var action_title = self._title
				self._rpc({
					model: 'account.general.ledger',
					method: 'get_accounts_line',
					args: [
						[self.wizard_id], account_id, action_title
					],
				}).then(function(data) {
					//                    _.each(data['report_lines'], function(rep_lines) {
					//                            _.each(rep_lines['move_lines'], function(move_line) {
					//
					//                             move_line.debit = self.format_currency(data['currency'],move_line.debit);
					//                            move_line.credit = self.format_currency(data['currency'],move_line.credit);
					//                            move_line.balance = self.format_currency(data['currency'],move_line.balance);
					//
					//
					//                             });
					//                             });

					for (var i = 0; i < data['report_lines'].length; i++) {
						if (account_id == data['report_lines'][i]['id']) {
							$(event.currentTarget).next('tr').find('td').remove();
							$(event.currentTarget).next('tr').after(
								QWeb.render('SubSection', {
									account_data: data['report_lines'][i]['move_lines'],
									currency_symbol: data.currency[0],
									id: data['report_lines'][i]['id'],
									currency_position: data.currency[1],

								}))
							$(event.currentTarget).next('tr').find('td ul li:first a').css({
								'background-color': '#fcba03',
								'font-weight': 'bold',
							});
						}
					}

				});
			}
		},

		view_acc_move: function(event) {
			event.preventDefault();
			var self = this;
			var context = {};
			var show_acc_move = function(res_model, res_id, view_id) {
				var action = {
					type: 'ir.actions.act_window',
					view_type: 'form',
					view_mode: 'form',
					res_model: res_model,
					views: [
						[view_id || false, 'form']
					],
					res_id: res_id,
					target: 'current',
					context: context,
				};
				return self.do_action(action);
			};
			rpc.query({
					model: 'account.move',
					method: 'search_read',
					domain: [
						['id', '=', $(event.currentTarget).data('move-id')]
					],
					fields: ['id'],
					limit: 1,
				})
				.then(function(record) {
					if (record.length > 0) {
						show_acc_move('account.move', record[0].id);
					} else {
						show_acc_move('account.move', $(event.currentTarget).data('move-id'));
					}
				});
		},

		apply_filter: function(event) {
			event.preventDefault();
			var self = this;
			self.initial_render = false;
			var filter_data_selected = {};

			//Account filter
			var account_ids = [];
			var account_text = [];
			var account_res = document.getElementById("account_res")
			var account_list = $(".account-partner").select2('data')
			for (var i = 0; i < account_list.length; i++) {
				if (account_list[i].element[0].selected === true) {
					account_ids.push(parseInt(account_list[i].id))
					if (account_text.includes(account_list[i].text) === false) {
						account_text.push(account_list[i].text)
					}
					account_res.value = account_text
					account_res.innerHTML = account_res.value;
				}
			}
			if (account_list.length == 0) {
				account_res.value = ""
				account_res.innerHTML = "";
			}
			filter_data_selected.account_ids = account_ids

			//Account Tag filter
			var account_tag_ids = [];
			var account_tag_text = [];
			var account_tag_res = document.getElementById("acc_tag_res")

			var account_tag_list = $(".account-tag").select2('data')
			for (var i = 0; i < account_tag_list.length; i++) {
				if (account_tag_list[i].element[0].selected === true) {

					account_tag_ids.push(parseInt(account_tag_list[i].id))
					if (account_tag_text.includes(account_tag_list[i].text) === false) {
						account_tag_text.push(account_tag_list[i].text)
					}

					account_tag_res.value = account_tag_text
					account_tag_res.innerHTML = account_tag_res.value;
				}
			}
			if (account_tag_list.length == 0) {
				account_tag_res.value = ""
				account_tag_res.innerHTML = "";

			}
			filter_data_selected.account_tag_ids = account_tag_ids

			//Journal Filter
			if (!(this._title == 'Bank Book' || this._title == 'Cash Book')) {
				var journal_ids = [];
				var journal_text = [];
				var journal_res = document.getElementById("journal_res")
				var journal_list = $(".journals").select2('data')
				for (var i = 0; i < journal_list.length; i++) {
					if (journal_list[i].element[0].selected === true) {
						journal_ids.push(parseInt(journal_list[i].id))
						if (journal_text.includes(journal_list[i].text) === false) {
							journal_text.push(journal_list[i].text)
						}
						journal_res.value = journal_text
						journal_res.innerHTML = journal_res.value;
					}
				}
				if (journal_list.length == 0) {
					journal_res.value = ""
					journal_res.innerHTML = "";
				}
				filter_data_selected.journal_ids = journal_ids
			}

			//Analytic Filter
			var analytic_ids = [];
			var analytic_text = [];
			var analytic_res = document.getElementById("analytic_res")
			var analytic_list = $(".analytics").select2('data')
			for (var i = 0; i < analytic_list.length; i++) {
				if (analytic_list[i].element[0].selected === true) {
					analytic_ids.push(parseInt(analytic_list[i].id))
					if (analytic_text.includes(analytic_list[i].text) === false) {
						analytic_text.push(analytic_list[i].text)
					}
					analytic_res.value = analytic_text
					analytic_res.innerHTML = analytic_res.value;
				}
			}
			if (analytic_list.length == 0) {
				analytic_res.value = ""
				analytic_res.innerHTML = "";
			}
			filter_data_selected.analytic_ids = analytic_ids

			//Date range filter
			if (this.$el.find('.datetimepicker-input[name="gen_date_from"]').val()) {
				filter_data_selected.date_from = moment(this.$el.find('.datetimepicker-input[name="gen_date_from"]').val(),
					time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
			}
			if (this.$el.find('.datetimepicker-input[name="gen_date_to"]').val()) {
				filter_data_selected.date_to = moment(this.$el.find('.datetimepicker-input[name="gen_date_to"]').val(),
					time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
			}

			//Target Move Filter
			if ($(".target_move").length) {
				var post_res = document.getElementById("post_res")
				filter_data_selected.target_move = $(".target_move")[1].value
				post_res.value = $(".target_move")[1].value
				post_res.innerHTML = post_res.value;
				if ($(".target_move")[1].value == "") {
					post_res.innerHTML = "posted";
				}
			}
			rpc.query({
				model: 'account.general.ledger',
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
	core.action_registry.add("g_l", GeneralLedger);
	return GeneralLedger;
});