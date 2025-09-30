/** @odoo-module */

import dom from '@web/legacy/js/core/dom';
import publicWidget from '@web/legacy/js/public/public_widget';
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
//     * Odoo customer contact form widget.
//     *
//     * This widget handles the behavior of the customer contact edit form on the website. It listens to specific events and
//     * performs corresponding actions when triggered.
//     */
publicWidget.registry.WebsiteCustomerContactEdit = publicWidget.Widget.extend({
    selector: '.customer_contact_edit_form',
    events: {
        'click #form_submit': 'validateNumber',
    },
//         /**
//         * Validate the input value of the #phone,#mobile fields to ensure it contains
//           only valid numbers.
//         *
//         * @param {Event} ev - The "input" event object.
//         */
       validateNumber: function (ev) {
          const mobile_no = this.$('#mobile');
          const phone_no = this.$('#phone');
          if ((!/^\d+$/.test(mobile_no.val())) || (!/^\d+$/.test(phone_no.val()))) {
            ev.preventDefault()
            this.call('dialog', 'add', AlertDialog, {
            title: _t("Warning!"),
            body: _t("Enter Valid Phone Number and Mobile Number"),
        });
          }
          return;
        },
});
