odoo.define("website_customer_contact.customer_contact_edit_form",
    function (require) {
        "use strict";
        let publicWidget = require("web.public.widget");
        const { _t } = require("web.core");
        const Dialog = require("web.Dialog");
        // Odoo customer contact form widget.
        publicWidget.registry.WebsiteCustomerEditContactRequestForm = publicWidget.Widget.extend({
            selector: ".customer_contact_edit_form",
            events: {
              "input #phone": "validateNumber",
              "input #mobile_number": "validateNumber",
            },
            // Validate the input value of the #phone field to ensure it contains only valid numbers.
            validateNumber: function (ev) {
                const input = this.$(ev.currentTarget);
                if (!/^\d+$/.test(input.val())) {
                    this.$("#warranty_submit").attr("disabled", "disabled");
                    return new Dialog(null, {
                      title: "Error:",
                      size: "medium",
                      $content: `<p>${
                        _.str.escapeHTML("Enter Valid Number ") || ""
                      }</p>`,
                      buttons: [{ text: _t("Ok"), close: true }],
                    }).open();
                } else {
                  this.$("#warranty_submit").removeAttr("disabled");
                }
                return;
            },
        });
        return publicWidget;
    }
);
