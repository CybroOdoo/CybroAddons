/**
 * This file is used to give a success alert after requesting a call for price.
 */
odoo.define('call_for_price_website.create_call_form', function(require) {
    "use strict";
    const rpc = require('web.rpc');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var publicWidget = require('web.public.widget');

    publicWidget.registry.CallForPrice = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click #send_btn': 'callForPrice',
            'click #button_call_for_price': 'modalShow',
            'click #call_modal_close': 'modalHide'
        },
        callForPrice: function() {
            var self = this;
            var first = self.$el.find('#first_name').val();
            var last = self.$el.find('#last_name').val();
            var product_id = self.$el.find('#product_id').val();
            var phone = self.$el.find('#phone').val();
            var email = self.$el.find('#email').val();
            var message = self.$el.find('#message').val();
            var qty = self.$el.find('#quantity').val();
            /**
             * Validate email address format using a regular expression.
             * email - The email address to validate.
             * returns - True if the email is valid, false otherwise.
             */
            function validateEmail(email) {
                // Email validation regex pattern
                var emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailPattern.test(email);
            }
            /**
             * Validate phone number format using a regular expression.
             * phone - The phone number to validate.
             * returns - True if the phone number is valid, false otherwise.
             */
            function validatePhoneNumber(phone) {
                // Phone number validation regex pattern (without alphabets)
                var phonePattern = /^[^A-Za-z]*$/
                return phonePattern.test(phone);
            }
            if (first && phone) {
                if (!$.isNumeric(qty)) {
                    var modal = new Dialog(null, {
                        title: "Warning",
                        $content: $('<div>').text("Quantity should be a numeric value."),
                        buttons: [{
                            text: "Close",
                            close: true
                        }],
                    });
                    modal.open();
                    return;
                }
                if (!validateEmail(email)) {
                    var modal = new Dialog(null, {
                        title: "Warning",
                        $content: $('<div>').text("Please enter a valid email address."),
                        buttons: [{
                            text: "Close",
                            close: true
                        }],
                    });
                    modal.open();
                    return;
                }
                if (!validatePhoneNumber(phone)) {
                    var modal = new Dialog(null, {
                        title: "Warning",
                        $content: $('<div>').text("Please enter a valid phone number."),
                        buttons: [{
                            text: "Close",
                            close: true
                        }],
                    });
                    modal.open();
                    return;
                }
                rpc.query({
                    model: "call.price",
                    method: "create_form",
                    args: [first, last, product_id, phone, email, message, qty]
                }).then(function(result) {
                    self.$el.find('#alert_message')[0].style.display = "block"
                    self.$el.find('#call_for_price')[0].style.display = 'none';
                });
            } else {
                var modal = new Dialog(null, {
                    title: "Warning",
                    $content: $('<div>').text("Please enter the required information."),
                    buttons: [{
                        text: "Close",
                        close: true
                    }],
                });
                modal.open();
            }
        },
        modalShow: function() {
            this.resetFormFields();
            this.$el.find('#call_for_price')[0].style.display = 'block';
        },
        modalHide: function() {
            this.$el.find('#call_for_price')[0].style.display = 'none';
        },
        resetFormFields: function() {
            this.$el.find('#first_name').val('');
            this.$el.find('#last_name').val('');
            this.$el.find('#email').val('');
            this.$el.find('#phone').val('');
            this.$el.find('#quantity').val('');
            this.$el.find('#message').val('');
        },

    });
    return publicWidget.registry.CallForPrice;
});