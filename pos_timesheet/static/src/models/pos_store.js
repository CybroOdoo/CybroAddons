/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

function normalizeSessionId(sessionId) {
    if (sessionId && typeof sessionId === "object") {
        return sessionId.id || null;
    }
    return Number.isInteger(sessionId) ? sessionId : Number(sessionId) || null;
}

function getCurrentSessionId(pos) {
    return normalizeSessionId(pos.session?.id || pos.config?.current_session_id);
}

patch(PosStore.prototype, {
    get employeeIsAdmin() {
        return !!this.cashier && this.cashier._role === "manager";
    },

    setup() {
        this.cashier = false;
        this.workedTime = [];
        return super.setup(...arguments);
    },

    async processServerData() {
        await super.processServerData(...arguments);
        if (this.config.module_pos_hr && (this.config.time_log || this.config.is_time_log)) {
            this.timesheet = this.models['account.analytic.line'].getAll();
            this.workedTime = [];

            if (Array.isArray(this.timesheet)) {
                const currentTaskId = this.session?.task_id?.id || this.session?.task_id || this.config?.task_id?.id || this.config?.task_id;
                const sessionTimesheets = this.timesheet.filter(data => {
                    const taskId = data.task_id?.id || data.task_id;
                    return taskId === currentTaskId;
                });

                sessionTimesheets.forEach((data) => {
                    const cashierId = data.employee_id?.id || data.employee_id;
                    const minutes = Math.floor((data.unit_amount || 0) * 60);
                    if (!cashierId || minutes <= 0) {
                        return;
                    }

                    const existingEntry = this.workedTime.find((entry) => entry.cashierId === cashierId);
                    if (existingEntry) {
                        existingEntry.minutes += minutes;
                    } else {
                        this.workedTime.push({ cashierId, minutes });
                    }
                });
            }
            this.ensureActiveCashierTimesheet();
        }
    },

    async closePos() {
        if (this.config.module_pos_hr && (this.config.time_log || this.config.is_time_log)) {
            const data = this.prepareTimesheet();
            try {
                await this.sendTimesheet(data);

                if (this.session?.task_id) {
                    try {
                        const action = await this.env.services.orm.call(
                            'pos.session',
                            'show_time_log',
                            [getCurrentSessionId(this)]
                        );
                        if (action && this.env.services.action) {
                            await this.env.services.action.doAction(action);
                        }
                    } catch (error) {
                        console.error("Error triggering time log view:", error);
                    }
                }

                this.workedTime = [];
                localStorage.setItem('timesheetData', JSON.stringify([]));
            } catch (error) {
                console.error("Error in closePos:", error);
            }
        }
        return super.closePos(...arguments);
    },

    resetCashier() {
        const previousCashierId = this.cashier?.id;
        const result = super.resetCashier(...arguments);
        if (this.config.module_pos_hr && (this.config.time_log || this.config.is_time_log)) {
            this._syncTimesheetInBackground(previousCashierId);
        }
        return result;
    },

    setCashier(employee) {
        const previousCashierId = this.cashier?.id;
        const result = super.setCashier(...arguments);
        if (this.config.module_pos_hr && (this.config.time_log || this.config.is_time_log)) {
            this._syncTimesheetInBackground(previousCashierId, employee);
        }
        return result;
    },

    async _syncTimesheetInBackground(previousCashierId, employee = null) {
        try {
            const data = this.prepareTimesheet(previousCashierId);
            if (data && data.length > 0 && getCurrentSessionId(this)) {
                await this.sendTimesheet(data);
            }
            this.setTimesheet([], employee);
        } catch (error) {
            console.error("Error in _syncTimesheetInBackground:", error);
        }
    },

    setTimesheet(timesheetData, employee = null) {
        try {
            let existingData = this.getStoredTimesheetData();

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
                const sessionId = getCurrentSessionId(this);
                existingData = existingData.filter(
                    entry => !(entry.cashierId === employee.id && entry.sessionId === sessionId && !entry.checkOutTime)
                );
                existingData.push({
                    cashierId: employee.id,
                    checkInTime: Date.now(),
                    sessionId,
                    syncedMinutes: 0,
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

        const validTimesheetData = timesheetData.filter(data => data.workMinutes > 0).map(data => ({
            cashierId: data.cashierId,
            workMinutes: data.workMinutes,
            checkInTime: data.checkInTime,
            sessionId: normalizeSessionId(data.sessionId) || getCurrentSessionId(this),
        }));
        if (validTimesheetData.length === 0) {
            return null;
        }
        console.log("Timesheet: Sending data to server:", validTimesheetData);
        try {
            await this.env.services.orm.call(
                'pos.session',
                'set_timesheet',
                [[getCurrentSessionId(this)], validTimesheetData],
            );

            const storedTimesheetData = this.getStoredTimesheetData();
            const currentSessionId = getCurrentSessionId(this);
            validTimesheetData.forEach(data => {
                if (normalizeSessionId(data.sessionId) === currentSessionId) {
                    const index = this.workedTime.findIndex(item => item.cashierId === data.cashierId);
                    if (index !== -1) {
                        this.workedTime[index].minutes += data.workMinutes;
                    } else {
                        this.workedTime.push({
                            cashierId: data.cashierId,
                            minutes: data.workMinutes
                        });
                    }
                }

                const storedEntry = storedTimesheetData.find(entry =>
                    entry.cashierId === data.cashierId &&
                    entry.checkInTime === data.checkInTime &&
                    normalizeSessionId(entry.sessionId) === normalizeSessionId(data.sessionId)
                );
                if (storedEntry) {
                    storedEntry.syncedMinutes = (storedEntry.syncedMinutes || 0) + data.workMinutes;
                }
            });
            localStorage.setItem('timesheetData', JSON.stringify(storedTimesheetData));
        } catch (error) {
            console.error("Failed to send timesheet:", error);
            throw error;
        }
    },

    prepareTimesheet(cashierId = null) {
        const timesheetData = this.getStoredTimesheetData();
        if (timesheetData.length === 0) return null;
        const sessionId = getCurrentSessionId(this);

        const activeEntry = [...timesheetData].reverse().find(entry =>
            !entry.checkOutTime &&
            (!cashierId || entry.cashierId === cashierId) &&
            normalizeSessionId(entry.sessionId) === sessionId
        );
        if (activeEntry) {
            activeEntry.checkOutTime = Date.now();
            const timeDiff = activeEntry.checkOutTime - activeEntry.checkInTime;
            activeEntry.workMinutes = Math.floor(timeDiff / (1000 * 60));
            localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
        }

        return timesheetData
            .map(data => {
                const pendingMinutes = this.getPendingWorkedMinutes(data);
                if (pendingMinutes <= 0) {
                    return null;
                }
                return {
                    cashierId: data.cashierId,
                    workMinutes: pendingMinutes,
                    checkInTime: data.checkInTime,
                    sessionId: data.sessionId,
                };
            })
            .filter(data => data && data.workMinutes > 0);
    },

    getStoredTimesheetData() {
        try {
            return JSON.parse(localStorage.getItem('timesheetData')) || [];
        } catch {
            return [];
        }
    },

    ensureActiveCashierTimesheet() {
        const cashierId = this.cashier?.id;
        const sessionID = getCurrentSessionId(this);
        if (!cashierId || !sessionID) {
            console.warn("Timesheet: Missing cashierId or sessionId", { cashierId, sessionID });
            return;
        }

        const timesheetData = this.getStoredTimesheetData();
        const hasActiveEntry = timesheetData.some(entry =>
            entry.cashierId === cashierId &&
            normalizeSessionId(entry.sessionId) === sessionID &&
            entry.checkInTime &&
            !entry.checkOutTime
        );

        if (!hasActiveEntry) {
            timesheetData.push({
                cashierId,
                checkInTime: Date.now(),
                sessionId: sessionID,
                syncedMinutes: 0,
            });
            localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
        }
    },

    getPendingWorkedMinutes(entry) {
        if (!entry?.workMinutes) {
            return 0;
        }
        return Math.max(0, entry.workMinutes - (entry.syncedMinutes || 0));
    },

    getActiveTimesheetEntry(cashierId = this.cashier?.id) {
        const sessionId = getCurrentSessionId(this);
        if (!cashierId || !sessionId) {
            return null;
        }
        const timesheetData = this.getStoredTimesheetData();
        return [...timesheetData].reverse().find(entry =>
            entry.cashierId === cashierId &&
            normalizeSessionId(entry.sessionId) === sessionId &&
            entry.checkInTime &&
            !entry.checkOutTime
        ) || null;
    },

    async syncActiveTimesheet() {
        const activeEntry = this.getActiveTimesheetEntry();
        if (!activeEntry?.checkInTime) {
            return;
        }

        const elapsedMinutes = Math.floor((Date.now() - activeEntry.checkInTime) / (1000 * 60));
        const pendingMinutes = elapsedMinutes - (activeEntry.syncedMinutes || 0);
        if (pendingMinutes <= 0) {
            return;
        }

        await this.sendTimesheet([{
            cashierId: activeEntry.cashierId,
            workMinutes: pendingMinutes,
            checkInTime: activeEntry.checkInTime,
            sessionId: activeEntry.sessionId,
        }]);
    }
});
