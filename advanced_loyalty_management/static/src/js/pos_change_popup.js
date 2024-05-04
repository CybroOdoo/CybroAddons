/** @odoo-module **/

import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
import { useService } from "@web/core/utils/hooks";
var rpc = require('web.rpc');

class LoyaltyPrograms extends AbstractAwaitablePopup {
    convertToLoyalty(props, programId,ev){
        //-----Change is converted to loyalty----
        var change = props.change
        const loyalty = props.Loyalty.filter(point => point.program.id ==programId)[0]
        var addedLoyalty = change * loyalty.program.point_rate
        props.Order.programToAdd = programId
        props.Order.convertToLoyalty = addedLoyalty
        props.Order.changeConverted = true
        const partner_id = props.Order.partner.id
        props.Order.getLoyaltyPoints()
        var convertLoyalty = rpc.query({
            model:'loyalty.program',
            method:'convert_loyalty',
            args:[programId,loyalty.couponId,addedLoyalty,partner_id]
        })
        ev.confirm()
    }

}
LoyaltyPrograms.template = 'LoyaltyPrograms';
    LoyaltyPrograms.defaultProps = {
        confirmText: 'Confirm',
        cancelText: 'Cancel',
        title: 'Loyalty Programs',
        body: '',
    };
Registries.Component.add(LoyaltyPrograms);
return LoyaltyPrograms;
