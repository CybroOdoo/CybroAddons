/** @odoo-module **/
import { PosModel } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

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
                    "This order already has refund lines for %s. We can't change the customer
                    associated to it. Create a new order for the new customer.",
                    currentPartner.name
                ),
            });
            return;
        }
        const { confirmed, payload: newPartner } = await this.showTempScreen("PartnerListScreen", {
            partner: currentPartner,
        });
        if (confirmed) {
            this.currentOrder.set_partner(newPartner);
            var washing=0
            for (let line of this.currentOrder.orderlines) {
               if (line.get_washingType())
               {
                    washing=1
               }
            }
            if (washing==0)
            {
                this.currentOrder.updatePricelist(newPartner);
            }
        }
    }
});
