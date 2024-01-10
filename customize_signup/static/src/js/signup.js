odoo.define('customize_signup.signup', function (require) {
'use strict';
var publicWidget = require('web.public.widget');
    const { _t } = require("web.core");
    const Dialog = require("web.Dialog");
publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
    selector: '.oe_signup_form',
    events: {
        'click #info': '_extraInfo',
        'click #hide_info': '_hideInfo',
        'click .btn-primary':'_signupBtn',
        "input #phone": "validateNumber",
        'change #file': 'validateImageFile',
    },
    /**
   * this method is used to store the information in the local storage
   */
    start: function(){
        if (localStorage.getItem('city')){
            this.$el.find('#city').val(localStorage.getItem('city'))
        }
        this.$el.find('#job_position').val(localStorage.getItem('job_position'))
        this.$el.find('#phone').val(localStorage.getItem('phone'))
        this.$el.find('#country').val(localStorage.getItem('country'))
    },
    _signupBtn:function (){
        localStorage.removeItem('city')
        localStorage.removeItem('job_position')
        localStorage.removeItem('phone')
        localStorage.removeItem('country');
    },
     /**
     * this method is used to show the extra information given in the
     *  signup form
     */
     _extraInfo: function () {
        this.$el.find("#data").toggle();
        if (info.style.display == 'none') {
            info.style.display = 'block';
        } else {
            info.style.display = 'none';
            hide_info.style.display = 'block';
        }
    },
    /**
     * this method is used to hide the extra information given in the
     *  signup form
     */
    _hideInfo: function () {
        this.$el.find("#data").toggle();
        if (hide_info.style.display == 'none') {
            hide_info.style.display = 'block';
        } else {
            hide_info.style.display = 'none';
            info.style.marginLeft= '-37px', info.style.display = 'block';
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
            return new Dialog(null, {
                title: "Error:",
                size: "medium",
                $content: `<p>${_.str.escapeHTML("Enter Valid Number ") || ""}</p>`,
                buttons: [{ text: _t("Ok"), close: true }],
            }).open();
        }
    }
    return;
},
validateImageFile: function (ev) {
    const fileInput = this.$(ev.currentTarget);
    const file = fileInput[0].files[0];

    if (file) {
        const allowedExtensions = /(\.jpg|\.jpeg|\.png|\.gif)$/i;

        if (!allowedExtensions.exec(file.name)) {
            fileInput.val(''); // Clear the file input
            return new Dialog(null, {
                title: 'Error:',
                size: 'medium',
                $content: '<p>Enter a valid image file (JPEG, JPG, PNG, GIF).</p>',
                buttons: [{ text: 'Ok', close: true }],
            }).open();
        }
    }
    return;
}
});
});
