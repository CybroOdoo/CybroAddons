/** @odoo-module **/

import ProductScreen from 'point_of_sale.ProductScreen';
import Registries from 'point_of_sale.Registries';

export const PoSSaleBeProductScreen = (ProductScreen) =>
    class extends ProductScreen {
        async onClickPartner() {
            // Override to check whether the laundry type already is added
            const currentPartner = this.currentOrder.get_partner();
            if (currentPartner && this.currentOrder.getHasRefundLines()) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t("Can't change customer"),
                    body: _.str.sprintf(
                        this.env._t(
                            "This order already has refund lines for %s. We can't change the customer associated to it. Create a new order for the new customer."
                        ),
                        currentPartner.name
                    ),
                });
                return;
            }
            const { confirmed, payload: newPartner } = await this.showTempScreen(
                'PartnerListScreen',
                { partner: currentPartner }
            );
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
    };
Registries.Component.extend(ProductScreen, PoSSaleBeProductScreen);
