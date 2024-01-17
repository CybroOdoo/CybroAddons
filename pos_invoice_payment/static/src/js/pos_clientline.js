odoo.define('pos_invoice_payment.ClientLine', function (require) {
  'use strict';
  /**
   * Import required modules.
   */
  const ClientLine = require('point_of_sale.ClientLine');
  const Registries = require('point_of_sale.Registries');
  /**
   * Extend the ClientLine component with additional functionality to show a popup for creating a payment.
   * @param {Class} ClientLine - The original ClientLine class to be extended.
   */
  const PosClientLine = (ClientLine) =>
    class extends ClientLine {
      /**
       * This method is called when the 'showPop' event is triggered.
       * It extracts the partner_id from the event's target element and sends an RPC request to fetch journals.
       * Then, it shows the 'CreatePaymentPopup' with the fetched journals and other relevant data.
       * @param {Object} ev - The event object containing information about the event.
       */
      async showPop(ev) {
        var partner_id = ev.target.parentElement.parentElement.attributes[1].value;
        var self = this;
        var journal_length = [];
        await this.rpc({
          model: "account.journal",
          method: "get_journal",
        }).then(function (result) {
          $.each(result, function (index, name) {
            journal_length.push(index);
          });
          self.showPopup("CreatePaymentPopup", {
            title: ("Create Payment"),
            confirmText: ("Exit"),
            journals: result,
            journal_length: journal_length,
            partner_id: partner_id
          });
        });
      }
    };
  /**
   * Extend the original ClientLine component with the new functionality provided by PosClientLine.
   */
  Registries.Component.extend(ClientLine, PosClientLine);
  /**
   * Export the extended ClientLine component.
   */
  return ClientLine;
});
