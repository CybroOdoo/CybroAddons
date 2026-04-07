/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

export class CreatePaymentPopup extends Component {
  // Extending AbstractAwaitablePopup And Adding A Popup
  static template = 'CreatePaymentPopup';
  static components = { Dialog };
  static props = {
    title: { type: String },
    journals: { type: Object },
    journal_length: { type: Array },
    partner_id: { type: Number, optional: true },
    currency_id: { type: Number, optional: true },
    confirmText: { type: String, optional: true },
    close: { type: Function },
  }
  setup() {
    super.setup();
    this.orm = useService("orm");
  }

  async confirm(ev) {
    let partner_id = ev['partner_id']
    let currency_id = ev['currency_id']
    let amount = document.getElementById("amount").value
    let journal_id = document.getElementById("journal").value

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

    let payment = await this.orm.call("account.payment", "create_payment", [values]);
    this.props.close();
  }

  cancel() {
    this.props.close();
  }
}
