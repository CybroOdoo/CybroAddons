/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CustomButtonPopup extends Component {
    static template = "custom_popup.CustomButtonPopup";
    static components = { Dialog };
    static defaultProps = {
        closePopup: _t("Cancel"),
        confirmText: _t("Save"),
        title: _t("Customer Details"),
    };
    setup() {
        this.orm = useService("orm");
    }
    convertToLoyalty(programId) {
        var change = Math.abs(this.props.change);
        const loyalty = this.props.loyalty_points.find(point => point.program.id == programId);
        if (!loyalty) {
            return;
        }
        var addedLoyalty = change * loyalty.program.point_rate;
        this.props.order.programToAdd = programId;
        this.props.order.convertToLoyalty = addedLoyalty;
        this.props.order.changeConverted = true;
        const partner = this.props.order.getPartner();
        if (!partner) {
            return;
        }
        const partner_id = partner.id;
        this.props.order.getLoyaltyPoints();
        this.props.close();
        // Use this.props.pos.data.call for Odoo 19 backend calls
        this.props.pos.data.call("loyalty.program", "convert_loyalty",
            [[programId], [loyalty.couponId], [addedLoyalty], [partner_id]]);
    }
}