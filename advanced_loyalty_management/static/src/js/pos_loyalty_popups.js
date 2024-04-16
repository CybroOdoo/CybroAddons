/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

export class CustomButtonPopup extends AbstractAwaitablePopup {
   static template = "custom_popup.CustomButtonPopup";
//   -------------------------------------
    setup(){
    this.orm = useService("orm");
    }
    convertToLoyalty(props, programId,ev){
        //-------change converted to loyalty points
        let convertToLoyalty = []
        var change = props.change
        const loyalty = props.loyalty_points.filter(point => point.program.id ==programId)[0]
        var addedLoyalty = change * loyalty.program.point_rate
        convertToLoyalty.push(addedLoyalty)
        props.order.programToAdd = programId
        props.order.convertToLoyalty = convertToLoyalty[0]
        props.order.changeConverted = true
        const partner_id = props.order.partner.id
        props.order.getLoyaltyPoints()
        props.close()
        const updateLoyalty = ev.orm.call("loyalty.program","convert_loyalty",
        [[programId],[loyalty.couponId],[convertToLoyalty[0]],[partner_id]])
    }
//   ----------------------------------------
   static defaultProps = {
       closePopup: _t("Cancel"),
       confirmText: _t("Save"),
       title: _t("Customer Details"),
   };
}