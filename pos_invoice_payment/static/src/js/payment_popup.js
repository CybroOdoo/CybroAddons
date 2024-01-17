/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
var core = require('web.core');
/**
 * This class represents a popup for creating a payment in the Point of Sale module.
 * It extends the AbstractAwaitablePopup class, which provides the basic structure and functionalities of a popup.
 */
class CreatePaymentPopup extends AbstractAwaitablePopup {
  setup() {
    super.setup();
  }
  /**
   * This method is triggered when the 'confirm' button is clicked.
   * It collects the input values from the popup, such as partner_id, currency_id, amount, and journal_id,
   * and sends an RPC request to create a payment using the provided data.
   * After processing the request, it triggers the "close-popup" event to close the popup.
   * @param {Object} ev - The event object containing the input values from the popup.
   */
  async confirm(ev) {
    var self=this;
    let partner_id = ev['partner_id'];
    let currency_id = ev['currency_id'];
    let amount = this.__owl__.pvnode.elm.querySelector("#amount").value
    let journal_id = this.__owl__.pvnode.elm.querySelector("#journal").value
     if (amount< 0) {
        this.__owl__.pvnode.elm.querySelector('#positive_validation').style.display='block'
    } else {
        var values = {};
    if (partner_id) {
      values["partner_id"] = partner_id;
    }
    if (journal_id) {
      values["journal_id"] = journal_id;
    }
    if (currency_id) {
      values["currency_id"] = currency_id;
    }
    if (amount) {
      values["amount"] = amount;
    }
    this.rpc({
      model: "account.payment",
      method: "create_payment",
      args: [values],
    }).then(function (result) {
    if(result){
        self.showNotification(_.str.sprintf(self.env._t('Created Successfully')),2000);
        self.trigger("close-popup", {
          popupId: self.props.id,
          response: {
            confirmed: false,
            payload: null,
         },
      });
    }
    });
    }
  }
}
CreatePaymentPopup.template = "CreatePaymentPopup";
Registries.Component.add(CreatePaymentPopup);
