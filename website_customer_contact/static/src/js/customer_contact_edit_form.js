/** @odoo-module */

import publicWidget from '@web/public/public_widget';
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

/**
 * Odoo customer contact edit form widget.
 *
 * This widget handles the behavior of the customer contact edit form
 * on the website. It listens to specific events and performs corresponding
 * actions when triggered.
 */
publicWidget.registry.WebsiteCustomerContactEdit = publicWidget.Widget.extend({
    selector: '.customer_contact_edit_form',
    events: {
        'click #form_submit': 'validateNumber',
    },
    /**
     * Validate the input value of the #phone field to ensure it contains
     * only valid numbers.
     *
     * @param {Event} ev - The event object.
     */
    validateNumber: function (ev) {
          const phone_no = this.$('#phone');
          if ((!/^\d+$/.test(phone_no.val()))) {
            ev.preventDefault()
            this.call('dialog', 'add', AlertDialog, {
            title: _t("Warning!"),
            body: _t("Enter Valid Phone Number"),
        });
          }
          return;
       },
});
