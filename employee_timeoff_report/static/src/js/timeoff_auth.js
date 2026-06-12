odoo.define('employee_timeoff_report.timeoff_auth', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.TimeoffAuthWidget = publicWidget.Widget.extend({
        selector: '#timeoff_auth_ui',
        events: {
            'click #btn_confirm_email': '_onConfirmEmail',
            'click #btn_authenticate': '_onAuthenticate',
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                // Force the field to be editable to override any core Odoo website behavior
                self.$('#timeoff_email_id').removeAttr('readonly').prop('readonly', false);
                self.$('#timeoff_email_id').removeAttr('disabled').prop('disabled', false);
            });
        },

        _onConfirmEmail: function (ev) {
            ev.preventDefault();
            var self = this;
            var email = this.$('#timeoff_email_id').val();
            var btn = $(ev.currentTarget);

            if (!email || !this._isValidEmail(email)) {
                this._showMessage('Please enter a valid email.', 'danger');
                return;
            }

            btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Processing...');

            ajax.jsonRpc('/my/timeoff/send_otp', 'call', { email: email }).then(function (result) {
                if (result.success) {
                    self.$('#otp_section').slideDown().removeClass('d-none');
                    self._showMessage('OTP successfully sent to your email.', 'success');
                    btn.html('Resend OTP').prop('disabled', false); // Allow resend logic if needed
                } else {
                    self._showMessage(result.message, 'danger');
                    btn.prop('disabled', false).text('Confirm');
                }
            }).catch(function () {
                self._showMessage('An error occurred. Please try again.', 'danger');
                btn.prop('disabled', false).text('Confirm');
            });
        },

        _onAuthenticate: function (ev) {
            ev.preventDefault();
            var self = this;
            var otp = this.$('#timeoff_otp_code').val();
            var btn = $(ev.currentTarget);

            if (!otp || otp.length < 4) {
                this._showMessage('Please enter a valid OTP.', 'danger');
                return;
            }

            btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Authenticating...');

            ajax.jsonRpc('/my/timeoff/authenticate', 'call', { otp: otp }).then(function (result) {
                if (result.success) {
                    self._showMessage('Authenticated! Redirecting...', 'success');
                    setTimeout(function() {
                        window.location.href = '/my/timeoff/success';
                    }, 1500);
                } else {
                    self._showMessage(result.message, 'danger');
                    btn.prop('disabled', false).text('Authenticated');
                }
            }).catch(function () {
                self._showMessage('Authentication failed.', 'danger');
                btn.prop('disabled', false).text('Authenticated');
            });
        },

        _isValidEmail: function (email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },

        _showMessage: function (msg, type) {
            var color = type === 'danger' ? '#dc3545' : '#198754';
            this.$('#auth_status_msg').text(msg).css('color', color).removeClass('d-none').hide().fadeIn();
        }
    });

    publicWidget.registry.TimeoffReportDashboardWidget = publicWidget.Widget.extend({
        selector: '#timeoff_report_dashboard',
        events: {
            'click .js_print_and_redirect': '_onPrintAndRedirect',
        },

        _onPrintAndRedirect: function (ev) {
            ev.preventDefault();
            var printUrl = $(ev.currentTarget).attr('href');

            // 1. Trigger the download in the current window. 
            // Browsers won't navigate away if the response is a file download.
            window.location.href = printUrl;

            // 2. Redirect to the logout route after a longer delay to ensure 
            // the download request is fully processed by the browser.
            setTimeout(function() {
                window.location.href = '/my/timeoff';
            }, 3000);
        },
    });
});
