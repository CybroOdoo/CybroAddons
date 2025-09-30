/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.landingSubscription = publicWidget.Widget.extend({
    selector: '.land_subscribe', // Target section
    events: {
        'click .submit_mail': '_onSubmitMailClick',
    },

    start: function () {
        console.log('Widget initialized');
        return this._super.apply(this, arguments);
    },

    _onSubmitMailClick: function (ev) {
        ev.preventDefault(); // Prevent default link behavior
        console.log('Submit button clicked!');

        const emailInput = this.$el.find("#textEmail").val();
        const emailDisplay = this.$el.find("#demo");
        const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

        const selectedAction = this.$el
            .find('input[name="radio"]:checked')
            .parent()
            .text()
            .trim()
            .toLowerCase();

        if (!emailRegex.test(emailInput)) {
            emailDisplay
                .css({ color: "#e74c3c", padding: "8px 0px" })
                .html(`❌ The email you entered isn't valid: <strong>${emailInput}</strong>`);
            return false;
        }

        if (selectedAction.includes("un")) {
            emailDisplay
                .css({ color: "#d9534f", padding: "8px 0px" })
                .html(
                    `<i class='fas fa-hand-point-left'></i> <strong>Unsubscribed</strong> successfully: ${emailInput}`
                );
        } else {
            emailDisplay
                .css({ color: "#50449c", padding: "8px 0px" })
                .html(
                    `<i class='fas fa-hand-point-right'></i> <strong>WOOHOO</strong> You subscribed successfully: ${emailInput}`
                );
        }



        this.$el.find("#textEmail").val('');

        return true;
    },
});
