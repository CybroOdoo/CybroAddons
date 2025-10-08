/** @odoo-module **/

import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";
    //Timesheet Button in Header of Pos
    class TimeSheetButton extends PosComponent {
       /**
        * Show WorkedHourPopup
        */
       async onClick(){
        await this.showPopup('WorkedHourPopup');
       }
    }
    TimeSheetButton.template = "TimeSheetButton";

    Registries.Component.add(TimeSheetButton);
