/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {

    setup(){
            this.workedTime = [];
            return super.setup(...arguments);

    },

    async _processData(loadedData) {
        await super._processData(...arguments);
        if (this.config.module_pos_hr && this.config.time_log) {
            this.timesheet = loadedData['account.analytic.line'];
            this.workedTime = [];
            const timesheetData = JSON.parse(localStorage.getItem('timesheetData')) || [];
            timesheetData.forEach(data => {
                if (data.cashierId && data.workMinutes) {
                    const existingEntry = this.workedTime.find(entry => entry.cashierId === data.cashierId);
                    if (existingEntry) {
                        existingEntry.minutes += data.workMinutes;
                    } else {
                        this.workedTime.push({ cashierId: data.cashierId, minutes: data.workMinutes });
                    }
                }
            });
        }
    },

    async closePos() {
        if (this.config.module_pos_hr && this.config.time_log) {
            const data = this.prepareTimesheet();
            try {
                await this.sendTimesheet(data);

                if (this.pos_session?.task_id) {
                    try {
                        const action = await this.env.services.orm.call(
                            'pos.session',
                            'show_time_log',
                            [this.pos_session.id]
                        );
                        if (action) {
                            this.env.pos.showPopup('ActionPopup', { action });
                        }
                    } catch (error) {
                        console.error("Error triggering time log view:", error);
                    }
                }

                this.workedTime = [];
                localStorage.setItem('timesheetData', JSON.stringify([]));
            } catch (error) {
                console.error("Error in closePos:", error);
                this.workedTime = [];
                localStorage.setItem('timesheetData', JSON.stringify([]));
            }
        }
        return super.closePos(...arguments);
    },

    reset_cashier() {
        if (this.config.module_pos_hr && this.config.time_log) {
            return this._handleTimesheet(() => super.reset_cashier(...arguments));
        }
        return super.reset_cashier(...arguments);
    },

    set_cashier(employee) {
        if (this.config.module_pos_hr && this.config.time_log) {
            return this._handleTimesheet(() => super.set_cashier(...arguments), employee);
        }
        return super.set_cashier(...arguments);
    },

    async _handleTimesheet(callback, employee = null) {
        try {
            const data = this.prepareTimesheet();
            if (data && data.length > 0) {
                await this.sendTimesheet(data);
            }
            this.setTimesheet(data, employee);
        } catch (error) {
            console.error("Error in _handleTimesheet:", error);
        } finally {
            callback();
        }
    },

    setTimesheet(timesheetData, employee = null) {
        try {
            let existingData = JSON.parse(localStorage.getItem('timesheetData')) || [];

            if (Array.isArray(timesheetData)) {
                timesheetData.forEach(newEntry => {
                    if (newEntry.cashierId && newEntry.workMinutes) {
                        const existingEntryIndex = existingData.findIndex(
                            entry => entry.cashierId === newEntry.cashierId &&
                                     entry.sessionId === newEntry.sessionId
                        );
                        if (existingEntryIndex !== -1) {
                            existingData[existingEntryIndex].workMinutes += newEntry.workMinutes;
                            existingData[existingEntryIndex].checkOutTime = newEntry.checkOutTime;
                        } else {
                            existingData.push(newEntry);
                        }
                    }
                });
            }

            if (employee) {
                existingData.push({
                    cashierId: employee.id,
                    checkInTime: Date.now(),
                    sessionId: this.config.current_session_id.id,
                });
            }

            localStorage.setItem('timesheetData', JSON.stringify(existingData));
        } catch (error) {
            console.error("Error in setTimesheet:", error);
        }
    },

    async sendTimesheet(timesheetData) {
        if (!timesheetData || !Array.isArray(timesheetData)) {
            return null;
        }

        const validTimesheetData = timesheetData.filter(data => data.workMinutes > 1).map(data => ({
            cashierId: data.cashierId,
            workMinutes: data.workMinutes,
            checkInTime: data.checkInTime,
            sessionId: this.config.current_session_id.id,
        }));
        if (validTimesheetData.length === 0) {
            return null;
        }
        try {
            const response = await this.env.services.orm.call(
                'pos.session',
                'set_timesheet',
                [[this.config.current_session_id.id], validTimesheetData],
            );

            validTimesheetData.forEach(data => {
                const index = this.workedTime.findIndex(item => item.cashierId === data.cashierId);
                if (index !== -1) {
                    this.workedTime[index].minutes += data.workMinutes;
                } else {
                    this.workedTime.push({
                        cashierId: data.cashierId,
                        minutes: data.workMinutes
                    });
                }
            });
        } catch (error) {
            console.error("Failed to send timesheet:", error);
            throw error;
        }
    },

    prepareTimesheet() {
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData')) || [];
        if (timesheetData.length === 0) return null;

        const lastEntry = timesheetData[timesheetData.length - 1];
        if (!lastEntry.checkOutTime) {
            lastEntry.checkOutTime = Date.now();
            const timeDiff = lastEntry.checkOutTime - lastEntry.checkInTime;
            lastEntry.workMinutes = Math.floor(timeDiff / (1000 * 60));
        }

        return timesheetData.filter(data => data.workMinutes > 1);
    }
});