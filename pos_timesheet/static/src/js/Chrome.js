/** @odoo-module **/

import Chrome from "point_of_sale.Chrome";
import Registries from "point_of_sale.Registries";


const PosTimeSheetChrome = (Chrome) =>
  class extends Chrome {


    /**
     * @override
     * Add timesheet in to server when go to backend
     */
    async _closePos() {
      if (this.env.pos.config.module_pos_hr & this.env.pos.config.time_log) {
         return this.env.pos._handleTimesheet(() => super._closePos(...arguments));
      } else {
        return await super._closePos(...arguments);
      }
    }

      /**
      *@override
         * Save Worked hours with CheckoutTime and WorkedMinutes in localStorage
         * on beforeunload - closing the browser, reloading or going to other page.
         */
        _onBeforeUnload() {
            super._onBeforeUnload(...arguments);
            const timesheetData = this.env.pos.prepareTimesheet();
            localStorage.setItem('timesheetData', JSON.stringify(timesheetData));
        }
  };

Registries.Component.extend(Chrome, PosTimeSheetChrome);
