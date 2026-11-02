/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, props, types } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CustomButtonPopup extends Component {
    static template = "advanced_loyalty_management.CustomButtonPopup";
    static components = { Dialog };
    props = props({
        loyalty_points: types.array,
        change: types.number,
        order: types.object,
        pos: types.object,
        close: types.function,
        closePopup: String,
        title: String,
    });
    setup() {
        this.orm = useService("orm");
    }
    async convertToLoyalty(programId) {
        var change = Math.abs(this.props.change);
        const loyalty = this.props.loyalty_points.find(point => point.program.id == programId);
        if (!loyalty) {
            return;
        }
        var addedLoyalty = change * loyalty.program.point_rate;
        const partner = this.props.order.getPartner();
        if (!partner) {
            return;
        }
        const partner_id = partner.id;

        await this.props.pos.data.call("loyalty.program", "convert_loyalty",
            [[programId], [loyalty.couponId], [addedLoyalty], [partner_id]]);
        const order = this.props.order;
        order.convertedChange = (order.convertedChange || 0) + change;
        order.changeConverted = true;
        this.props.close();
    }
}