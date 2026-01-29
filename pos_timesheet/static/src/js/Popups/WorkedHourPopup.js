odoo.define('point_of_sale.WorkedHourPopup', function(require) {
    'use strict';
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const { _lt } = require('@web/core/l10n/translation');
class WorkedHourPopup extends AbstractAwaitablePopup {
    /**
     * @super
         * Sets up: SetInterval to show realtime worked time.
     */
    setup() {
        super.setup(...arguments);
        this.state = owl.hooks.useState({
            workedTime: '',
            totalWorkedTime: ''
        })
        owl.hooks.onMounted(() => {
            this.workedTime();
            this.totalWorkedTime();
            this.interval = setInterval(()=>{
                  this.workedTime();
                  this.totalWorkedTime();
            }, 1000);
        })
        owl.hooks.onWillUnmount(() => {
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
        const cashierId = this.env.pos.get_cashier().id;
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
    }}
WorkedHourPopup.template = "pos_timesheet.WorkedHourPopup";
WorkedHourPopup.defaultProps = {
      cancelText: _lt("Cancel"),
      title: _lt("Worked Hours"),
      confirmKey: false,
};
Registries.Component.add(WorkedHourPopup);
return WorkedHourPopup;
});
