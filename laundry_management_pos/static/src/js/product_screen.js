/** @odoo-module **/
import { PosModel } from "@point_of_sale/app/store/pos_model";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/error_popup";
import { _t } from "@web/core/l10n/translation";

patch(PosModel.prototype, {
    //Override select partner method
    async selectPartner() {
        const currentOrder = this.get_order();
        if (!currentOrder) {
            return;
        }
        const currentPartner = currentOrder.get_partner();
        if (currentPartner && currentOrder.getHasRefundLines()) {
            this.popup.add(ErrorPopup, {
                title: _t("Can't change customer"),
                body: _t(
                    "This order already has refund lines for %s. We can't change the customer associated to it. Create a new order for the new customer.",
                    currentPartner.name
                ),
            });
            return;
        }
        const { confirmed, payload: new_partner } = await this.showTempScreen("PartnerListScreen", {
            partner: currentPartner,
        });
        if (confirmed) {
            this.currentOrder.set_partner(new_partner);
            let washing = 0
            for (let line of this.currentOrder.orderlines) {
                if (line.get_washing_type()) {
                    washing = 1
                }
            }
            if (washing == 0) {
                this.currentOrder.updatePricelist(new_partner);
            }
        }
    }
});
