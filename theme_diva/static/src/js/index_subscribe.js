/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.indexSubscription = publicWidget.Widget.extend({
    selector: '.subscribe',

    events: {
        'click .submit_index_mail': '_onSubmitMailClick',
    },

    _onSubmitMailClick: function () {
        console.log('Submit button clicked!');

        const emailInput = this.$el.find("#textEmail").val();
        const messageDisplay = this.$el.find("#demo");
        const emailRegex = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

        const selectedAction = this.$el
            .find('input[name="radio"]:checked')
            .parent()
            .text()
            .trim()
            .toLowerCase();

        if (!emailRegex.test(emailInput)) {
            messageDisplay
                .css({ color: "#535353", padding: "8px 0px" })
                .html(`The email you entered isn't valid: ${emailInput}`);
            return false;
        }

        if (selectedAction.includes('un')) {
            messageDisplay
                .css({ color: "#d9534f", padding: "8px 0px" })
                .html(
                    `<i class='fas fa-hand-point-left'></i> <strong>Unsubscribed</strong> successfully: ${emailInput}`
                );
        } else {
            messageDisplay
                .css({ color: "#50449c", padding: "8px 0px" })
                .html(
                    `<i class='fas fa-hand-point-right'></i> <strong>WOOHOO</strong> You subscribed successfully: ${emailInput}`
                );
        }

        return true;
    },
});
