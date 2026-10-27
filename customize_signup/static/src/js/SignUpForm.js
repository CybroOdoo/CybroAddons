/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";


publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
    selector: '.oe_signup_form',
    events: {
        'click #info': '_extraInfo',
        'click #hide_info': '_hideInfo',
        'click .btn-primary': '_signupBtn',
        'input #phone': 'validateNumber',
        'change #file': 'validateImageFile',
    },
    /**
     * this method is used to store the information in the local storage
     */
    init() {
        this._super.apply(this, arguments);
        this.notification = this.bindService("notification");
    },
    start: function () {
        if (localStorage.getItem('city')) {
            this.$el.find('#city').val(localStorage.getItem('city'));
        }
        this.$el.find('#job_position').val(localStorage.getItem('job_position'));
        this.$el.find('#phone').val(localStorage.getItem('phone'));
        this.$el.find('#country').val(localStorage.getItem('country'));
    },
    /**
     * Removes stored data from localStorage related to user signup information.
     */
    _signupBtn: function () {
        localStorage.removeItem('city');
        localStorage.removeItem('job_position');
        localStorage.removeItem('phone');
        localStorage.removeItem('country');
    },
    /**
     * this method is used to show the extra information given in the
     *  signup form
     */
    _extraInfo: function (ev) {
        if (ev) {
            ev.preventDefault();
        }
        this.$el.find("#data").toggle();
        const infoEl = this.$el.find('#info');
        const hideInfoEl = this.$el.find('#hide_info');
        if (infoEl.is(':hidden')) {
            infoEl.show();
        } else {
            infoEl.hide();
            hideInfoEl.show();
        }
    },
    /**
     * this method is used to hide the extra information given in the
     *  signup form
     */
    _hideInfo: function (ev) {
        if (ev) {
            ev.preventDefault();
        }
        this.$el.find("#data").toggle();
        const infoEl = this.$el.find('#info');
        const hideInfoEl = this.$el.find('#hide_info');
        if (hideInfoEl.is(':hidden')) {
            hideInfoEl.show();
        } else {
            hideInfoEl.hide();
            infoEl.css('marginLeft', '-37px');
            infoEl.show();
        }
    },
    /**
     * this method is used to validate phone number field given in the
     *  signup form
     */
    validateNumber: function (ev) {
        const input = this.$(ev.currentTarget);
        const inputValue = input.val();
        if (inputValue.length > 0) {
            if (!/^\d+$/.test(inputValue)) {
                input.val(''); // Clear the field
                this.notification.add(_t("Enter a valid number"), { type: 'danger' });
            }
        }
    },
    /**
     * this method is used to validate File field given in the
     *  signup form
     */
    validateImageFile: function (ev) {
        const fileInput = this.$(ev.currentTarget);
        const file = fileInput[0].files[0];

        if (file) {
            const allowedExtensions = /(\.jpg|\.jpeg|\.png|\.gif)$/i;
            if (!allowedExtensions.exec(file.name)) {
                fileInput.val('');
                this.notification.add(_t("Enter a valid image file"), { type: 'danger' });
            }
        }
    },
});
