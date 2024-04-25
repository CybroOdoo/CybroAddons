odoo.define('pos_timesheet.pos', function(require) {
	"use strict";
	const models = require('point_of_sale.models');
	const { DateTime } = luxon;
	var super_pos_model = models.PosModel.prototype;
	models.PosModel = models.PosModel.extend({
		     /** @override
		     * load employees timesheet of this session
		     */
		after_load_server_data: async function() {
			await this._processData();
			return super_pos_model.after_load_server_data.apply(this, arguments)
		},
		_processData: async function() {
			var self = this
			if (this.config.module_pos_hr && this.config.time_log) {
				this.models.push({
					model: 'account.analytic.line',
					fields: ['name', 'employee_id', 'id', 'unit_amount', 'date', 'task_id', 'pos_created'],
					loaded: function(self, analytic_lines) {
						self.timesheet = analytic_lines;
					},
				});
				var employee_list = [];
				for (const employee in this.employees){
				    employee_list.push(this.employees[employee].id)
				}
                var today = DateTime.local().c['day'] + '/' +
                DateTime.local().c['month'] + '/' + DateTime.local().c['year']
				var fields = ['employee_id', 'id', 'unit_amount',];
				var result = await this.env.services.rpc({
					model: 'account.analytic.line',
					method: 'search_read',
					kwargs: {
						domain: [['employee_id', 'in', employee_list],
						         ['pos_created', '=', true],
						         ['date', '=', today]],
						fields
					},
				})
				this.timesheet = result;
				this.workedTime = this.getWorkedTime();
			}
		},
		/** Retrieves worked time data and sets it to the POS instance. */
		getWorkedTime: function() {
			const datas = this.timesheet;
			const workedTime = datas.map(data => ({
				'cashierId': data['employee_id'][0],
				'minutes': Math.floor(data['unit_amount'] * 60)
			}));
			return workedTime;
		},
		/**
		 * @override
		 * If the 'Multi Employee persession' and 'Time Log' enabled in POS configuration,
		 * handles timesheet processing before setting cashier.
		 * @param {Object} employee - Employee object representing the cashier.
		 */
		set_cashier: function(employee) {
			this.super_set_cashier = super_pos_model.set_cashier.apply(this, arguments);
			if (this.config.module_pos_hr && this.config.time_log) {
				return this._handleTimesheet(this.get('cashier'));
			} else {
				return this.super_set_cashier;
			}
		},
		/**
		 * Handles timesheet processing asynchronously.
		 * Executes a callback function and handles timesheet operations based on the POS configuration.
		 * @param {Function} callback - Callback function to execute.
		 * @param {Object} employee - Employee object representing the cashier or null.
		 */
		_handleTimesheet: function(employee = null) {
			const data = this.prepareTimesheet();
			return this.sendTimesheet(data).then(response => {
					this.setTimesheet(response, employee);
				})
				.catch(errData => {
					this.setTimesheet(errData, employee);
				})
		},
		/**
		 * Sets the timesheet data to localStorage.
		 * @param {Array} timesheetData - Timesheet data to set.
		 * @param {Object} employee - Employee object representing the cashier.
		 */
		setTimesheet: function(timesheetData, employee = null) {
			if (employee) {
			    let cashierId;
                if (employee.id) {cashierId = employee.id}
                else {cashierId = null; }
				const cashierData = {
					cashierId: cashierId,
					checkInTime: Date.now(),
					sessionId: this.pos_session.id
				};
				if (timesheetData) {
					timesheetData.push(cashierData);
				} else {
					timesheetData = [cashierData];
				}
			}
			localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
		},
		/**
		 * Sends timesheet data to the server.
		 * @param {Array} timesheetData - Timesheet data to send.
		 * @return {null} success or no timesheetData, if error {Object} timesheetData
		 */
		sendTimesheet: function(timesheetData) {
			return new Promise((resolve, reject) => {
				if (timesheetData) {
					this.env.services.rpc({
							model: 'pos.session',
							method: 'set_timesheet',
							args: [
								[], timesheetData
							],
						}).then(res => {
							timesheetData.forEach(data => {
								let index = this.workedTime.findIndex(item => item.cashierId === data.cashierId);
								if (index !== -1) {
									this.workedTime[index].minutes += data.workMinutes;
								} else {
									this.workedTime.push({
										cashierId: data.cashierId,
										minutes: data.workMinutes
									});
								}
							});
							resolve(null);
						})
						.catch(err => {
							reject(timesheetData);
						});
				} else {
					resolve(null);
				}
			});
		},
		/**
		 * Prepares timesheet data for sending to the server.
		 * Checks for existing timesheet data in localStorage and adjusts work minutes.
		 * @returns {Array|null} Prepared timesheet data.
		 */
		prepareTimesheet: function() {
			const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
			if (timesheetData && timesheetData.length != 0) {
				if (!timesheetData.at(-1).hasOwnProperty('checkOutTime')) {
					timesheetData.at(-1)['checkOutTime'] = Date.now();
					const timeDiff = timesheetData.at(-1)['checkOutTime'] - timesheetData.at(-1)['checkInTime'];
					timesheetData.at(-1)['workMinutes'] = Math.floor(timeDiff / (1000 * 60));
					if (timesheetData.at(-1)['workMinutes'] <= 0) {
						timesheetData.pop();
					}
				}
				return timesheetData;
			}
			return null;
		},
	});
});