odoo.define('pos_invoice_payment.PartnerLine', function (require) {
  'use strict';
  // Import required modules
  const PartnerLine = require('point_of_sale.PartnerLine');
  const Registries = require('point_of_sale.Registries');
  /**
   * Extend the PartnerLine component with custom functionality.
   * @param {Object} PartnerLine - The original PartnerLine component.
   */
  const PosPartnerLine = (PartnerLine) =>
    class extends PartnerLine {
      /**
       * Show the CreatePaymentPopup for the selected partner.
       * @param {Object} ev - Event data.
       */
      async showPop(ev) {
        var partner_id = ev.target.parentElement.parentElement.attributes[1].value
        var self = this
        var journal_length = []

        // Retrieve journals and show CreatePaymentPopup
        await this.rpc({
          model: "account.journal",
          method: "get_journal",
        }).then(function (result) {
          $.each(result, function (index, name) {
            journal_length.push(index)
          })
          self.showPopup("CreatePaymentPopup", {
            title: ("Create Payment"),
            confirmText: ("Exit"),
            journals: result,
            journal_length: journal_length,
            partner_id: partner_id
          });
        })
      }
    };
  // Extend the PartnerLine component with PosPartnerLine
  Registries.Component.extend(PartnerLine, PosPartnerLine);
  // Return the extended PartnerLine component
  return PartnerLine;
});
