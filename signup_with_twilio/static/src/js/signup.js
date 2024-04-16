/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.SignUpFormExtension = publicWidget.Widget.extend({
    selector: '.oe_signup_form_mobile, .oe_reset_password_form',
    events: {
        'click .sent-otp': '_onClick',
        'change .check_login': '_onClickCheck',
        'click button[type="submit"]': '_onSubmitClick',
    },
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    _onClick: function (ev) {
        /** OTP will be create and collect the to number and redirected
        to the twilio function o send the otp, and enable the signup
        button to signup the user **/
        ev.stopPropagation();
        ev.preventDefault();
        this.$('.sign-up').removeAttr('disabled');
        this.$('.sent-otp').attr('disabled','disabled');
        const CountryCode = $(".div_code")[0].value
        const Mobile = $(".login_mobile")[0].value
        let OTP = '';
        var digits = '0123456789';
        for (let i = 0; i < 4; i++ ) {
            OTP += digits[Math.floor(Math.random() * 10)];
        }
        window.localStorage.setItem("OTP", OTP)
         this.rpc('/web/send_otp', {
            'country_code' : CountryCode,
            'mobile': Mobile,
            'otp': OTP,
        })
    },
    _onSubmitClick: function (ev) {
        /**Signup button will check the sent and receive otp to block the
        user creation if it is not same, and also enable the otp button to
        send the sms again  **/
        this.$('.sent-otp').removeAttr('disabled');
        let otp_val = $("#sms_otp_verify")[0].value
        let OTP = window.localStorage.getItem("OTP")
        if (OTP && otp_val && OTP != otp_val){
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

