/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
/**
 * CreatePaymentPopup component for creating a payment.
 * Extends AbstractAwaitablePopup.
 */
class CreatePaymentPopup extends AbstractAwaitablePopup {
  /**
   * Setup method for the CreatePaymentPopup component.
   */
  setup() {
    super.setup();
  }
  /**
   * Confirm method for creating the payment.
   * @param {Object} ev - Event data containing partner_id, currency_id, and other values.
   */
  async confirm(ev) {
    let partner_id = ev['partner_id']
    let currency_id = ev['currency_id']
    let amount = $("#amount").val();
    let journal_id = $("#journal").val();
    var values = {}
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
    })
    this.env.posbus.trigger("close-popup", {
      popupId: this.props.id,
      response: {
        confirmed: false,
        payload: null,
      },
    });
  }
}
// Template for CreatePaymentPopup component
CreatePaymentPopup.template = "CreatePaymentPopup";
// Register CreatePaymentPopup component
Registries.Component.add(CreatePaymentPopup);
