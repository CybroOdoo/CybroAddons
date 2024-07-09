/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"
import { _t } from "@web/core/l10n/translation";

export const customXtream = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        'click .input-group-append': 'onClickSubscribe',
    },
    // Startup functions
    start() {
        this.rpc = this.bindService("rpc");
        $('.qtyplus').click(function (e) {
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            fieldName = $(this).attr('field');
            // Get its current value
            var currentVal = parseInt($('input[name=' + fieldName + ']').val());
            // If is not undefined
            if (!isNaN(currentVal)) {
                // Increment
                $('input[name=' + fieldName + ']').val(currentVal + 1);
            } else {
                // Otherwise put a 0 there
                $('input[name=' + fieldName + ']').val(0);
            }
        });
        // This button will decrement the value till 0
        $(".qtyminus").click(function (e) {
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            fieldName = $(this).attr('field');
            // Get its current value
            var currentVal = parseInt($('input[name=' + fieldName + ']').val());
            // If it isn't undefined or its greater than 0
            if (!isNaN(currentVal) && currentVal > 0) {
                // Decrement one
                $('input[name=' + fieldName + ']').val(currentVal - 1);
            } else {
                // Otherwise put a 0 there
                $('input[name=' + fieldName + ']').val(0);
            }
        });
    },
    counter() {
        var buttons = $('.owl-dots button');
        buttons.each(function (item) {
        });
    },
    async onClickSubscribe(ev) {
        var $button = $(ev.currentTarget).find('span')
        var $input = $(ev.currentTarget.parentElement).find('input')
        if (this.emailCheck($input.val())) {
            if ($button.text() === "SUBSCRIBE") {
                await this.rpc('/subscribe_newsletter', {
                    email: $input.val()
                }).then(function (data) {
                    if (data) {
                        $(ev.currentTarget.parentElement.parentElement).find(
                            '.warning').hide()
                        $input.css('pointer-events', 'none')
                        $button.css('background-color', 'green')
                        $button.text("THANKS")
                    } else {
                        $(ev.currentTarget.parentElement.parentElement).find(
                            '.warning').text("Already subscribed to the newsletter.")
                        $(ev.currentTarget.parentElement.parentElement).find(
                            '.warning').show()
                    }
                })
            }
        } else {
            $(ev.currentTarget.parentElement.parentElement).find(
                '.warning').text("Enter a valid email.")
            $(ev.currentTarget.parentElement.parentElement).find(
                '.warning').show()
        }
    },
    emailCheck(str) {
        const specialChars = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return specialChars.test(str)
    }
})

PublicWidget.registry.customXtream = customXtream
