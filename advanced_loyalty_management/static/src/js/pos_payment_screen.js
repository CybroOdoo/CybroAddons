/** @odoo-module **/
import PaymentScreenStatus from 'point_of_sale.PaymentScreenStatus';
import Registries from 'point_of_sale.Registries' ;
const { Gui } = require('point_of_sale.Gui');

const ChangeLoyalty = (PaymentScreenStatus) =>
    class extends PaymentScreenStatus {
        convertLoyalty(){
            //----A pop is added to choose to which loyalty card the program is added
            var order = this.env.pos.get_order()
            var loyaltyPoints = order.getLoyaltyPoints()
            var change = order.get_change()
            if(loyaltyPoints.length != 0){
                Gui.showPopup("LoyaltyPrograms", {
                    title: this.env._t('Convert Change'),
                    cancelText: this.env._t("Cancel"),
                    confirmText:this.env._t("Confirm"),
                    Order:order,
                    change:change,
                    Loyalty :loyaltyPoints,
                });
            }
        }
    }
Registries.Component.extend(PaymentScreenStatus, ChangeLoyalty)
