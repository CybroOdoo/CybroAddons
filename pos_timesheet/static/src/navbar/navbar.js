/** @odoo-module */
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { useState, onWillStart, useExternalListener, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);

        this.state = useState({
            currentSessionTime: "00:00",
            totalWorkedTime: "00:00"
        });

        this.beforeUnload = () => {
            try {
                const existingData = JSON.parse(localStorage.getItem('timesheetData')) || [];
                const lastEntry = existingData.at(-1);

                if (lastEntry && !lastEntry.checkOutTime) {
                    lastEntry.checkOutTime = Date.now();
                    const timeDiff = lastEntry.checkOutTime - lastEntry.checkInTime;
                    lastEntry.workMinutes = Math.floor(timeDiff / (1000 * 60));
                    localStorage.setItem('timesheetData', JSON.stringify(existingData));
                }
            } catch (error) {
                console.error("Error in beforeUnload:", error);
            }
        };

        this.updateDisplayedTimes = () => {
            this.state.currentSessionTime = this.workedTime;
            this.state.totalWorkedTime = this.totalWorkedTime;
        };

        onWillStart(() => this.initializeTimeTracking());
        onWillUnmount(() => {
            if (this.timeUpdateInterval) {
                clearInterval(this.timeUpdateInterval);
            }
        });
        useExternalListener(window, 'beforeunload', this.beforeUnload);
    },

    initializeTimeTracking() {
        try {
            if (!this.pos.workedTime) {
                this.pos.workedTime = [];
            }

            const timesheetData = this.getTimesheetData();
            if (timesheetData.length > 0) {
                timesheetData.forEach(data => {
                    if (data.cashierId && data.workMinutes) {
                        const existingEntry = this.pos.workedTime.find(entry => entry.cashierId === data.cashierId);
                        if (existingEntry) {
                            existingEntry.minutes += data.workMinutes;
                        } else {
                            this.pos.workedTime.push({ cashierId: data.cashierId, minutes: data.workMinutes });
                        }
                    }
                });
            }

            if (typeof this.getWorkedTime === 'function') {
                this.getWorkedTime();
            }

            this.updateDisplayedTimes();
            this.timeUpdateInterval = setInterval(this.updateDisplayedTimes, 1000);
        } catch (error) {
            console.error("Error initializing time tracking:", error);
        }
    },

    getWorkedTime() {
        try {
            if (!Array.isArray(this.pos.timesheet)) {
                this.pos.workedTime = [];
                return;
            }

            const workedTime = this.pos.timesheet.map(data => ({
                'cashierId': data['employee_id']?.[0] || null,
                'minutes': Math.floor((data['unit_amount'] || 0) * 60),
            })).filter(data => data['cashierId']);

            workedTime.forEach(newEntry => {
                const existingEntry = this.pos.workedTime.find(entry => entry.cashierId === newEntry.cashierId);
                if (existingEntry) {
                    existingEntry.minutes += newEntry.minutes;
                } else {
                    this.pos.workedTime.push(newEntry);
                }
            });
        } catch (error) {
            console.error("Error in getWorkedTime:", error);
            this.pos.workedTime = [];
        }
    },

    get checkInTime() {
        try {
            const timesheetData = this.getTimesheetData();
            if (!timesheetData?.at(-1)?.checkInTime) {
                return new Intl.DateTimeFormat('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: true
                }).format(Date.now());
            }
            return new Intl.DateTimeFormat('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            }).format(timesheetData.at(-1).checkInTime);
        } catch (error) {
            console.error("Error in checkInTime:", error);
            return "--:--";
        }
    },

    get workedTime() {
        try {
            const [hours, minutes] = this.calculateCurrentSessionTime();
            return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
        } catch (error) {
            console.error("Error in workedTime:", error);
            return "00:00";
        }
    },

    get totalWorkedTime() {
        try {
            const cashierId = this.pos.cashier?.id;
            if (!cashierId) return '00:00';

            let totalMinutes = this.calculateTotalWorkedMinutes(cashierId);

            if (this.isClockInActive()) {
                const [currentHours, currentMinutes] = this.calculateCurrentSessionTime();
                totalMinutes += currentHours * 60 + currentMinutes;
            }

            const hours = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;
            return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
        } catch (error) {
            console.error("Error in totalWorkedTime:", error);
            return "00:00";
        }
    },

    getTimesheetData() {
        try {
            return JSON.parse(localStorage.getItem('timesheetData')) || [];
        } catch (error) {
            console.error("Error reading timesheet data:", error);
            return [];
        }
    },

    isClockInActive() {
        try {
            const timesheetData = this.getTimesheetData();
            const lastEntry = timesheetData.at(-1);
            return lastEntry?.checkInTime && !lastEntry?.checkOutTime;
        } catch (error) {
            console.error("Error in isClockInActive:", error);
            return false;
        }
    },

    calculateCurrentSessionTime() {
        try {
            const timesheetData = this.getTimesheetData();
            const lastEntry = timesheetData.at(-1);

            if (!this.isClockInActive()) {
                return [0, 0];
            }

            const currentTime = Date.now();
            const differenceMs = currentTime - lastEntry.checkInTime;
            const hours = Math.floor(differenceMs / (1000 * 60 * 60));
            const minutes = Math.floor((differenceMs % (1000 * 60 * 60)) / (1000 * 60));
            return [hours, minutes];
        } catch (error) {
            console.error("Error in calculateCurrentSessionTime:", error);
            return [0, 0];
        }
    },

    calculateTotalWorkedMinutes(cashierId) {
        try {
            let totalMinutes = 0;

            const timesheetData = this.getTimesheetData();
            if (timesheetData) {
                const cashierEntries = timesheetData.filter(
                    data => data.cashierId === cashierId && data?.workMinutes
                );
                totalMinutes += cashierEntries.reduce((sum, data) => sum + data.workMinutes, 0);
            }

            const cashierData = this.pos.workedTime.find(data => data.cashierId === cashierId);
            if (cashierData) {
                totalMinutes += parseInt(cashierData.minutes) || 0;
            }

            return totalMinutes;
        } catch (error) {
            console.error("Error in calculateTotalWorkedMinutes:", error);
            return 0;
        }
    }
});
