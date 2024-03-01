/** @odoo-module */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { useState, onWillStart, useExternalListener } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(Navbar.prototype, {
     /**
     * @override
     * Sets up event listeners.
     */
    setup() {
        super.setup(...arguments);
        onWillStart(this.getWorkedTime);
        useExternalListener(window, 'beforeunload', this.beforeUnload.bind(this));
    },

    /**
     * @override
     * Add timesheet in to server when Close Session.
     */
     async closeSession() {
         if (this.pos.config.module_pos_hr && this.pos.config.time_log) {
            return this.pos._handleTimesheet(() => super.closeSession(...arguments));
        } else {
            return super.closeSession(...arguments);
        }
    },

     /**
     * Event handler triggered before the window unloads.
     * eg:- leave the pos by changing the url or closing website etc..
     * set CheckoutTime and WorkedMinutes save in to session.
     */
    beforeUnload() {
        const timesheetData = this.pos.prepareTimesheet();
        localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
    },

    /**
     * Retrieves worked time data and sets it to the POS instance.
     */
    getWorkedTime() {
        const datas = this.pos.timesheet;
        const workedTime = datas.map(data => ({
            'cashierId': data['employee_id'][0],
            'minutes': Math.floor(data['unit_amount'] * 60)
        }));
        this.pos.workedTime = workedTime;
    },

    /**
     * Getter for the check-in time.
     * @returns {string} Formatted check-in time.
     */
    get checkInTime() {
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
        const checkInTime = timesheetData ? timesheetData.at(-1)['checkInTime'] : Date.now();
        const formattedDate = new Intl.DateTimeFormat('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        }).format(checkInTime);
        return formattedDate;
    },

     /**
     * Getter for the current worked time.
     * @returns {string} Formatted current worked time.
     */
    get workedTime() {
        const [hours, minutes] = this.currentWorkedTime();
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    },

    /**
     * Getter for the total today's worked time.
     * @returns {string} Formatted total worked time.
     */
    get totalWorkedTime() {
        let minutes = 0;
        const workerData = this.pos.workedTime;
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
        const cashierId = this.pos.cashier.id;

        if (timesheetData) {
            const cashierLocalTimesheet = timesheetData.filter(data => data.cashierId === cashierId && data?.workMinutes);
            minutes += cashierLocalTimesheet.reduce((sum, data) => sum + data.workMinutes, 0);
        }

        const cashierData = workerData.find(data => data['cashierId'] === cashierId);
        minutes += cashierData ? parseInt(cashierData['minutes']) : 0;

        const [currentHours, currentMinutes] = this.currentWorkedTime();
        let hours = currentHours;
        minutes += currentMinutes;

        const extraHour = Math.floor(minutes / 60);
        minutes %= 60;
        hours += extraHour;

        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    },

    /**
     * Retrieves the current worked time.
     * @returns {Array} Array containing hours and minutes of current worked time.
     */
     currentWorkedTime() {
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
        const checkInTime = timesheetData ? timesheetData.at(-1)['checkInTime'] : Date.now();
        const currentTime = Date.now();
        const differenceMs = Math.abs(currentTime - checkInTime);
        const hours = Math.floor(differenceMs / (1000 * 60 * 60));
        const minutes = Math.floor((differenceMs % (1000 * 60 * 60)) / (1000 * 60));
        return [hours, minutes];
    }

});
