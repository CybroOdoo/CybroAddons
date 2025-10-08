/** @odoo-module **/

import ClosePosPopup from "point_of_sale.ClosePosPopup";
import Registries from "point_of_sale.Registries";

const NewClosePosPopup = (ClosePosPopup) =>
  class extends ClosePosPopup {

    /**
     * @override
     * Add timesheet in to server when Close Session.
     */
    async closeSession() {
      if (this.env.pos.config.module_pos_hr & this.env.pos.config.time_log) {
        return this.env.pos._handleTimesheet(() =>
          super.closeSession(...arguments)
        );
      } else {
        return await super.closeSession(...arguments);
      }
    }
  };

Registries.Component.extend(ClosePosPopup, NewClosePosPopup);
