/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.SignUpFormExtension = publicWidget.Widget.extend({
    selector: '.oe_signup_form_mobile, .oe_reset_password_form',
    events: {
        'click .sent-otp': '_onClick',
        'change .check_login': '_onClickCheck',
        'click button[type="submit"]': '_onSubmitClick',
        'input #country_code_search': '_onCountryCodeSearch',
        'focus #country_code_search': '_onCountryCodeFocus',
        'click .country-code-option': '_onCountryCodeSelect',
    },
    init() {
        this._super(...arguments);
        this._boundCloseDropdown = this._closeDropdown.bind(this);
    },
    start() {
        document.addEventListener('click', this._boundCloseDropdown);
        return this._super(...arguments);
    },
    destroy() {
        document.removeEventListener('click', this._boundCloseDropdown);
        return this._super(...arguments);
    },
    _onCountryCodeFocus: function () {
        /** Show all options when the search field is focused **/
        this._showDropdown();
        this.$('.country-code-option').show();
    },
    _onCountryCodeSearch: function () {
        /** Filter country code options based on search text **/
        const query = this.$('#country_code_search').val().toLowerCase().replace('+', '').trim();
        const $options = this.$('.country-code-option');
        $options.each(function () {
            const name = $(this).data('name').toLowerCase();
            const code = String($(this).data('code'));
            const matches = name.includes(query) || code.includes(query);
            $(this)[matches ? 'show' : 'hide']();
        });
        this._showDropdown();
    },
    _onCountryCodeSelect: function (ev) {
        /** When a country is selected, store the code and update the visible input **/
        const $item = $(ev.currentTarget);
        const code = $item.data('code');
        this.$('#selected_country_code').val(code);
        this.$('#country_code_search').val('+' + code);
        this._hideDropdown();
    },
    _showDropdown: function () {
        this.$('#country_code_dropdown').show();
    },
    _hideDropdown: function () {
        this.$('#country_code_dropdown').hide();
    },
    _closeDropdown: function (ev) {
        /** Close dropdown when clicking outside the search wrapper **/
        const $wrapper = this.$('.country-code-search-wrapper');
        if ($wrapper.length && !$wrapper[0].contains(ev.target)) {
            this._hideDropdown();
        }
    },
    _onClick: function (ev) {
        /** OTP will be create and collect the to number and redirected
        to the twilio function o send the otp, and enable the signup
        button to signup the user **/
        ev.stopPropagation();
        ev.preventDefault();
        this.$('.sign-up').removeAttr('disabled');
        this.$('.sent-otp').attr('disabled', 'disabled');
        const CountryCode = this.$('#selected_country_code').val() || this.$('#country_code_search').val().replace(/[^0-9]/g, '');
        const Mobile = $(".login_mobile")[0].value;
        let OTP = '';
        var digits = '0123456789';
        for (let i = 0; i < 4; i++) {
            OTP += digits[Math.floor(Math.random() * 10)];
        }
        window.localStorage.setItem("OTP", OTP)
        rpc('/web/send_otp', {
            'country_code': CountryCode,
            'mobile': Mobile,
            'otp': OTP,
        })
    },
    _onSubmitClick: function (ev) {
        /**Signup button will check the sent and receive otp to block the
        user creation if it is not same, and also enable the otp button to
        send the sms again  **/
        this.$('.sent-otp').removeAttr('disabled');

        // Ensure country_code is set even if user just typed it without selecting from list
        if (!this.$('#selected_country_code').val()) {
            const searchVal = this.$('#country_code_search').val().replace(/[^0-9]/g, '');
            if (searchVal) {
                this.$('#selected_country_code').val(searchVal);
            }
        }

        let otp_val = $("#sms_otp_verify")[0].value
        let OTP = window.localStorage.getItem("OTP")
        if (OTP && otp_val && OTP != otp_val) {
            ev.preventDefault();
            alert('OTP is not matching');
        }
    },
    _onClickCheck: function (ev) {
        /**This will update the email page if it has the same login**/
        let checked = $('.check_login')[0].checked
        if (checked) {
            $('#login_mail')[0].value = $(".field-login")[0].children[1].value
        }
    },
});
