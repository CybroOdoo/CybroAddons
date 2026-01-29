odoo.define('website_signup_approval.FormValidation', function (require) {
'use strict';

const publicWidget = require('web.public.widget');
//Validation widget class for sign up form validation
publicWidget.registry.FormValidation = publicWidget.Widget.extend({
    selector: '.oe_website_login_container',
    events: {
        'keyup .oe_signup_form input[name="confirm_password"]': '_checkPassword',
        'keyup .oe_signup_form input[name="password"]': '_checkPassword',
        'change .oe_import_file': '_onFileChange'
    },
    //Check weather attached file type is a supported one
     _onFileChange: function (event) {
        const fileInput = event.currentTarget;
        const file = fileInput.files[0];
        this.$el.find('.document-alert').hide();
        if (file) {
            const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg'];
            if (!allowedTypes.includes(file.type)) {
                this.$el.find('.document-alert').show();
                fileInput.value = '';  // Clear the file input
                this.$el.find('button[type="submit"]').prop('disabled', true);
            } else {
                this.$el.find('button[type="submit"]').prop('disabled', false);
            }
        }
    },
    //Check password and confirm Password are same
    _checkPassword: function(event){
        if(this.$el.find("#confirm_password").val() != ''){
            if (this.$el.find("#password").val() === this.$el.find("#confirm_password").val()) {
                this.$el.find('.pass-alert').hide();
                this.$el.find('button[type="submit"]').prop('disabled', false);
            }
            else{
                this.$el.find('.pass-alert').show();
                this.$el.find('button[type="submit"]').prop('disabled', true);
            }
        }
        else{
            this.$el.find('.pass-alert').hide();
        }
    },
});
return publicWidget.registry.FormValidation;
});
