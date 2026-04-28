/** @odoo-module */

      /**
     * Age Verification Widget for Odoo Website.
     *
     * This widget handles the age verification process for users trying to sign up on the Odoo website.
     * It displays a modal asking users to confirm their date of birth and checks if the user is at least
     * 18 years old. If the user is 18 or older, the sign-up form is enabled; otherwise, an access
     * denied message is shown.
     */
    import publicWidget from "@web/legacy/js/public/public_widget";
    publicWidget.registry.age_verification = publicWidget.Widget.extend({
        selector: ".oe_website_login_container",
        events: {
            'click #age_confirmed': 'onClickAgeConfirm',
        },
        start: function() {
            this._super.apply(this, arguments);
            this._showAgeVerificationModal();
        },
        _showAgeVerificationModal: function () {
            var emailField = $('#signup_form input[name="login"]').val();
            var passwordField = $('#signup_form input[name="password"]').val();
            if (emailField) {
                this.$el.find('.age-verify').hide();
            }
        },
        onClickAgeConfirm: function(e) {
            var date = this.$el.find('#start').val();
            var dob = new Date(date);
            var currentDate = new Date();
            var timeDiff = currentDate.getTime() - dob.getTime();
            var age = Math.floor(timeDiff / (1000 * 60 * 60 * 24 * 365.25));
            if (age >= 18) {
                this.$el.find('.age-verify').hide();
                this.$el.find('.oe_signup_form :input').prop('disabled', false);
                sessionStorage.setItem('ageVerified', true);
            } else {
                this.$el.find('.access_message').removeClass('d-none');
            }
        },
    });
