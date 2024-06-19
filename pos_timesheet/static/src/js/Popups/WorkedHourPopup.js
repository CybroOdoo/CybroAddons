/** @odoo-module **/

import Registries from "point_of_sale.Registries";
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import { _lt } from "@web/core/l10n/translation";

const { onMounted, onWillUnmount, useState } = owl;



class WorkedHourPopup extends AbstractAwaitablePopup {
    /**
     * @override
         * Sets up SetInterval to show realtime worked time.
     */
    setup() {
        super.setup(...arguments);
        this.state = useState({
            workedTime: '',
            totalWorkedTime: ''
        })
        onMounted(()=> {
            this.workedTime();
            this.totalWorkedTime();
            this.interval = setInterval(()=>{
                  this.workedTime();
                  this.totalWorkedTime();
            }, 1000);
        })
        onWillUnmount(()=> {
            clearInterval(this.interval);
        })

    }


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
    }

     /**
     * Getter for the current worked time.
     * Assign {string} Formatted current worked time in to this.state.workedTime.
     */
    workedTime() {
        const [hours, minutes, seconds] = this.currentWorkedTime();
        this.state.workedTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    /**
     * Getter for the total today's worked time.
     * Assign {string} Formatted total worked time in to this.state.totalWorkedTime.
     */
    totalWorkedTime() {
        let minutes = 0;
        const workerData = this.env.pos.workedTime;
        const timesheetData = JSON.parse(localStorage.getItem('timesheetData'));
        const cashierId = this.env.pos.cashier.id;

        if (timesheetData) {
            const cashierLocalTimesheet = timesheetData.filter(data => data.cashierId === cashierId && data?.workMinutes);
            minutes += cashierLocalTimesheet.reduce((sum, data) => sum + data.workMinutes, 0);
        }

        const cashierData = workerData.find(data => data['cashierId'] === cashierId);

        minutes += cashierData ? parseInt(cashierData['minutes']) : 0;

        const [currentHours, currentMinutes, seconds] = this.currentWorkedTime();
        let hours = currentHours;
        minutes += currentMinutes;

        const extraHour = Math.floor(minutes / 60);
        minutes %= 60;
        hours += extraHour;

        this.state.totalWorkedTime =  `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

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
        const seconds = Math.floor((differenceMs % (1000 * 60)) / 1000);
        return [hours, minutes, seconds];
    }

}
WorkedHourPopup.template = "WorkedHourPopup";
WorkedHourPopup.defaultProps = {
  cancelText: _lt("Cancel"),
  title: _lt("Worked Hours"),
  confirmKey: false,
};

Registries.Component.add(WorkedHourPopup);
