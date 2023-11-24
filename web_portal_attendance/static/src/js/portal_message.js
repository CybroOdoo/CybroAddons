odoo.define('web_portal_attendance.leaving_message', function (require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
    var currentTime = new Date().getHours();

    var Slider = PublicWidget.Widget.extend({
        selector: '.flex-grow-1',
        start: function () {
            var self = this;
            self.leaving_message();
            self.welcome_message();
        },
//Function for adding leaving message in the tag
        leaving_message: function () {
            var leavingNoteElement = this.$el.find("#leaving_message");
            if (leavingNoteElement.length) { // Check if the element exists
                if (currentTime < 12) {
                    leavingNoteElement.text("Have a good day!"); // Set the text
                } else if (currentTime < 18) {
                    leavingNoteElement.text("Have a great lunch!"); // Set the text
                } else if (currentTime < 24) {
                    leavingNoteElement.text("Have a good tea time!"); // Set the text
                } else {
                    leavingNoteElement.text("Have a great sleep!"); // Set the text
                }
            }
        },
//Function for adding welcome message in the tag
        welcome_message: function () {
            var welcomeNoteElement = this.$el.find(".welcome_note");
            if (welcomeNoteElement.length) { // Check if the element exists
                if (currentTime < 12) {
                    welcomeNoteElement.text("Good Morning!"); // Set the text
                } else if (currentTime < 18) {
                    welcomeNoteElement.text("Good Afternoon!"); // Set the text
                } else if (currentTime < 24) {
                    welcomeNoteElement.text("Good Evening!"); // Set the text
                } else {
                    welcomeNoteElement.text("Good Night!"); // Set the text
                }
            }
        },
    });
    PublicWidget.registry.banner = Slider;
    return Slider;
});
