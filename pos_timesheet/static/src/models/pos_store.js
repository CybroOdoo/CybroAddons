/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { PosTicketPrinterPlugin } from "@point_of_sale/app/plugins/pos_ticket_printer_plugin";

patch(PosTicketPrinterPlugin.prototype, {
    initDefaultPrinter() {
        if (!this.config) {
            return;
        }
        return super.initDefaultPrinter(...arguments);
    },

    async initPrinters() {
        if (!this.config) {
            return;
        }
        return super.initPrinters(...arguments);
    },

    get receiptPrinters() {
        return this.config?.receipt_printer_ids || [];
    },

    get preparationPrinters() {
        return this.config?.preparation_printer_ids || [];
    },

    get printerStorageKey() {
        const configId = this.config?.id || (typeof odoo !== "undefined" && odoo.pos_config_id) || "";
        return `pos_default_printer_id_${configId}_${typeof odoo !== "undefined" && odoo.info?.db}`;
    },
});

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
    get cashier() {
        return this.accessRight?.loggedCashier || this.user || null;
    },

    get employeeIsAdmin() {
        return !!this.cashier && this.cashier._role === "manager";
    },

    setup() {
        this.workedTime = [];
        return super.setup(...arguments);
    },

    async processServerData() {
        await super.processServerData(...arguments);
        if (this.config.module_pos_hr && this.config.time_log) {
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
                    const minutes = Math.round((data.unit_amount || 0) * 60);
                    if (!cashierId || minutes <= 0) {
                        return;
                    }

                    const existingEntry = this.workedTime.find((entry) => String(entry.cashierId) === String(cashierId));
                    if (existingEntry) {
                        existingEntry.minutes += minutes;
                    } else {
                        this.workedTime.push({ cashierId, minutes });
                    }
                });
            }

            this.ensureActiveCashierTimesheet();
            await this.syncPendingTimesheets();
        }
    },

    async closePos() {
        if (this.config.module_pos_hr && this.config.time_log) {
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
        if (this.config.module_pos_hr && this.config.time_log) {
            this._syncTimesheetInBackground(previousCashierId);
        }
        return result;
    },

    setCashier(employee) {
        const previousCashierId = this.cashier?.id;
        const result = super.setCashier(...arguments);
        if (this.config.module_pos_hr && this.config.time_log) {
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
                    const index = this.workedTime.findIndex(item => String(item.cashierId) === String(data.cashierId));
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
                    String(entry.cashierId) === String(data.cashierId) &&
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
            (!cashierId || String(entry.cashierId) === String(cashierId)) &&
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
        let activeEntry = timesheetData.find(entry =>
            String(entry.cashierId) === String(cashierId) &&
            normalizeSessionId(entry.sessionId) === sessionID &&
            entry.checkInTime &&
            !entry.checkOutTime
        );

        if (!activeEntry) {
            const now = Date.now();
            const closedEntry = [...timesheetData].reverse().find(entry =>
                String(entry.cashierId) === String(cashierId) &&
                normalizeSessionId(entry.sessionId) === sessionID &&
                entry.checkInTime &&
                entry.checkOutTime &&
                (now - entry.checkOutTime) < 300000
            );
            if (closedEntry) {
                delete closedEntry.checkOutTime;
                delete closedEntry.workMinutes;
                activeEntry = closedEntry;
                localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
            }
        }

        if (!activeEntry) {
            const serverAccumulated = this.workedTime.find(item => String(item.cashierId) === String(cashierId));
            const serverMinutes = serverAccumulated ? serverAccumulated.minutes : 0;
            timesheetData.push({
                cashierId,
                checkInTime: Date.now(),
                sessionId: sessionID,
                syncedMinutes: serverMinutes,
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
            String(entry.cashierId) === String(cashierId) &&
            normalizeSessionId(entry.sessionId) === sessionId &&
            entry.checkInTime &&
            !entry.checkOutTime
        ) || null;
    },

    async syncPendingTimesheets() {
        const timesheetData = this.getStoredTimesheetData();
        if (!timesheetData || timesheetData.length === 0) {
            return;
        }
        const sessionId = getCurrentSessionId(this);
        if (!sessionId) {
            return;
        }

        const now = Date.now();
        const pendingEntries = [];

        timesheetData.forEach(entry => {
            if (normalizeSessionId(entry.sessionId) !== sessionId) {
                return;
            }

            let elapsedMinutes = 0;
            if (entry.checkOutTime) {
                elapsedMinutes = typeof entry.workMinutes === 'number'
                    ? entry.workMinutes
                    : Math.floor((entry.checkOutTime - entry.checkInTime) / (1000 * 60));
            } else {
                elapsedMinutes = Math.floor((now - entry.checkInTime) / (1000 * 60));
            }

            const pendingMinutes = elapsedMinutes - (entry.syncedMinutes || 0);
            if (pendingMinutes > 0) {
                pendingEntries.push({
                    cashierId: entry.cashierId,
                    workMinutes: pendingMinutes,
                    checkInTime: entry.checkInTime,
                    sessionId: entry.sessionId,
                });
            }
        });

        if (pendingEntries.length > 0) {
            await this.sendTimesheet(pendingEntries);
        }
    },

    async syncActiveTimesheet() {
        await this.syncPendingTimesheets();
    }
});
