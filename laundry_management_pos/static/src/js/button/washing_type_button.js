/**@odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { LaundryServiceTypePopup } from "@laundry_management_pos/js/popup/washing_type_popup";

export class WashingButton extends Component {
    static template = "point_of_sale.WashingButton";
    async setup() {
        this.pos = usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
        await this.loadDataFromWashingTypeModel();
    }
    //Click function of opening the popup.
    async onClick() {
        this.popup.add(LaundryServiceTypePopup, {
            title: _t('Laundry Service'),
            body: _t('Choose the Washing type'),
            service: this.pos.washing_type,
            pos: this.pos,
            orderline: this.props.line,
        })
    }
     async loadDataFromWashingTypeModel() {
        // Method for loading washing types
            const washingTypeData = await this.orm.call(
                'washing.type',
                'search_read',
                [],
                {
                    fields: ['name', 'assigned_person', 'amount']
                }
            );
            this.pos.washing_type = washingTypeData;
     }
}
ProductScreen.addControlButton({
component: WashingButton,
condition: function () {
 return true;
 },
});
