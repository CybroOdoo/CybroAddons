/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
     /**
     * @override
     */
    async _processData(loadedData) {
        await super._processData(...arguments);
        if (this.config.module_pos_hr && this.config.time_log) {
            this.timesheet = loadedData['account.analytic.line'];
            this.workedTime = [];
        }
    },

     /**
     * @override
     * Add timesheet in to server when go to backend
     */
    async closePos() {
         if (this.config.module_pos_hr && this.config.time_log) {
            return this._handleTimesheet(() => super.closePos(...arguments));
        } else {
            return super.closePos(...arguments);
        }
    },

    /**
     * @override
     * If the 'Multi Employee persession' and 'Time Log' enabled in POS configuration,
     * handles timesheet processing before resetting the cashier.
     */

    reset_cashier() {
        if (this.config.module_pos_hr && this.config.time_log) {
            return this._handleTimesheet(() => super.reset_cashier(...arguments));
        } else {
            return super.reset_cashier(...arguments);
        }
    },

     /**
     * @override
     * If the 'Multi Employee persession' and 'Time Log' enabled in POS configuration,
     * handles timesheet processing before setting the cashier.
     * @param {Object} employee - Employee object representing the cashier.
     */
    set_cashier(employee) {
        if (this.config.module_pos_hr && this.config.time_log) {
            return this._handleTimesheet(() => super.set_cashier(...arguments), employee);
        } else {
            return super.set_cashier(...arguments);
        }
    },

     /**
     * Handles timesheet processing asynchronously.
     * Executes a callback function and handles timesheet operations based on the POS configuration.
     * @param {Function} callback - Callback function to execute.
     * @param {Object} employee - Employee object representing the cashier or null.
     */

    _handleTimesheet(callback, employee = null) {
        const data = this.prepareTimesheet();
        return this.sendTimesheet(data)
            .then(response => {
                this.setTimesheet(response, employee);
            })
            .catch(errData => {
                this.setTimesheet(errData, employee);
            })
            .finally(() => {
                callback();
            });
    },

    /**
     * Sets the timesheet data to localStorage.
     * @param {Array} timesheetData - Timesheet data to set.
     * @param {Object} employee - Employee object representing the cashier.
     */
    setTimesheet(timesheetData, employee = null) {
        if (employee) {
            const cashierData = {
                cashierId: employee.id,
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
    sendTimesheet(timesheetData) {
        return new Promise((resolve, reject) => {
            if (timesheetData) {
                this.orm.call('pos.session', 'set_timesheet', ['', timesheetData])
                    .then(res => {
                        timesheetData.forEach(data => {
                            let index = this.workedTime.findIndex(item => item.cashierId === data.cashierId);
                            if (index !== -1) {
                                this.workedTime[index].minutes += data.workMinutes;
                            } else {
                                this.workedTime.push({ cashierId: data.cashierId, minutes: data.workMinutes });
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
    prepareTimesheet() {
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
        if (timesheetData && timesheetData.length != 0){
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
    }
});
