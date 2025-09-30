/** @odoo-module */

import dom from '@web/legacy/js/core/dom';
import publicWidget from '@web/legacy/js/public/public_widget';
import { Dialog } from "@web/core/dialog/dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
//     * Odoo customer contact form widget.
//     *
//     * This widget handles the behavior of the customer contact request form
//       on the website. It listens to specific events and
//     * performs corresponding actions when triggered.
//     */
publicWidget.registry.WebsiteCustomerContactRequest = publicWidget.Widget.extend({
    selector: '.customer_contact_form',
    events: {
        'click #contact_request_form_submit ': 'validateNumber',
        "change .select_box_test": "_onChangeType",
        "change .country_select": "_onChangeCountry",
    },
//         /**
//         * Validate the input value of the #phone,#mobile fields to ensure it
//           contains only valid numbers.
//         *
//         * @param {Event} ev - The "input" event object.
//         */
        validateNumber: function (ev) {
          const mobile_no = this.$('#mobile_number');
          const phone_no = this.$('#phone_number');
          if ((!/^\d+$/.test(mobile_no.val())) || (!/^\d+$/.test(phone_no.val()))) {
            ev.preventDefault()
            this.call('dialog', 'add', AlertDialog, {
            title: _t("Warning!"),
            body: _t("Enter Valid Phone Number and Mobile Number"),
        });
          }
          return;
        },

        // Onchange of customer type, fields to fill varies
        _onChangeType: function (ev) {
          let select = this.$(ev.currentTarget);
          let selectedValue = select.val();
          if (selectedValue === "contact") {
            this.$el.find(".job_position").show();
            this.$el.find(".contact_title").show();
            this.$el.find(".street").hide();
            this.$el.find(".street2").hide();
            this.$el.find(".city").hide();
            this.$el.find(".zip").hide();
            this.$el.find(".state_id").hide();
            this.$el.find(".country_id").hide();
          } else {
            this.$el.find(".job_position").hide();
            this.$el.find(".contact_title").hide();
            this.$el.find(".street").show();
            this.$el.find(".street2").show();
            this.$el.find(".city").show();
            this.$el.find(".zip").show();
            this.$el.find(".state_id").show();
            this.$el.find(".country_id").show();
          }
        },

        // Onchange of country, only states of that particular country will be shown
        _onChangeCountry: function (ev) {
          let selected_country =
            this.$el.find(".country_select")[0].selectedOptions[0].innerText;
          let state = this.$el.find(".state_select_option");
          for (let i = 0; i < state.length; i++) {
            state[i].style["display"] = "";
            if (state[i].dataset["id"] != selected_country) {
              state[i].style["display"] = "none";
            }
          }
        },
});
