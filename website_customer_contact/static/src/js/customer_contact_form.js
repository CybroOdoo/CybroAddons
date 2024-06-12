odoo.define("website_customer_contact.customer_contact_form", function (require) {
    "use strict";
    let publicWidget = require("web.public.widget");
    const { _t } = require("web.core");
    const Dialog = require("web.Dialog");
    publicWidget.registry.WebsiteCustomerContactRequestForm = publicWidget.Widget.extend({
        selector: ".customer_contact_form",
        events: {
          "change .select_box_test": "_onChangeType",
          "change .country_select": "_onChangeCountry",
          "input #phone_number": "validateNumber",
          "input #mobile_number": "validateNumber",
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
        /**
         * Handle the onchange event for the country selection.
         * Show only the states of the selected country and hide others.
         */
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
        /**
         * Validate the input value of the phone and mobile number fields to ensure they contain only valid numbers.
         * If an invalid number is entered, it displays an error dialog with a corresponding message.
         */
        validateNumber: function (ev) {
          const input = this.$(ev.currentTarget);
          if (!/^\d+$/.test(input.val())) {
            this.$("#contact_request_form_submit").attr("disabled", "disabled");
            return new Dialog(null, {
              title: "Error:",
              size: "medium",
              $content: `<p>${
                _.str.escapeHTML("Enter Valid Number ") || ""
              }</p>`,
              buttons: [{ text: _t("Ok"), close: true }],
            }).open();
          } else {
            this.$("#contact_request_form_submit").removeAttr("disabled");
          }
          return;
        },
      });
    return publicWidget;
  }
);
