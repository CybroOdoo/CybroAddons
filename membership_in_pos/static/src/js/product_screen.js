/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { Order } from "@point_of_sale/app/store/models";
import { useService } from "@web/core/utils/hooks";

patch(Order.prototype, {
       async pay() {
          if (this.partner){
               if (this.orderlines.some((line) => line.get_product().tracking !== "none" && !line.has_valid_product_lot()) && (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)){
                  const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                      title: _t("Some Serial/Lot Numbers are missing"),
                      body: _t("You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?"),
                      confirmText: _t("Yes"),
                      cancelText: _t("No"),
                  });
                  if (confirmed) {
                       this.pos.mobile_pane = "right";
                       this.env.services.pos.showScreen("PaymentScreen");
                  }
               } else {
                     this.pos.mobile_pane = "right";
                     this.env.services.pos.showScreen("PaymentScreen");
               }
               super.pay()
          }
         else{
             this.env.services.popup.add(ErrorPopup, {
                     title: _t("Customer"),
                     body :  _t("You Must Select a Customer"),
             });
         }

       }
})
