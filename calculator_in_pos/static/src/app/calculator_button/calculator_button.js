/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { CalculatorPopup } from "../calculator_popup/calculator_popup.js";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/* This class represents calculator button in product screen. */
export class CalculatorButton extends Component{
    static template = "CalculatorButton";
    /* Initializes the component and sets up necessary dependencies. */
    setup() {
        super.setup();
        this.pos = usePos();
        this.popup = useService("popup");
    }
     /**
     * Handles the click event of the CalculatorButton.
     * Opens a popup for calculator.
     */
    async click() {
        await this.popup.add(CalculatorPopup, {
            title: _t('Calculator'),
        });
    }
}
/* Adding CalculatorButton to the ProductScreen controls */
ProductScreen.addControlButton({
    component: CalculatorButton,
    condition: function() {
        return this.pos.config.active_calc;
    },
});
