/** @odoo-module **/
/**
 * This JavaScript file defines a publicWidget called 'suspicious' for the login form.
 * It extends the publicWidget.Widget class from the Odoo web module.
 * The 'suspicious' widget handles the login process and adds additional functionality.
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
var otpFieldAdded = false;
publicWidget.registry.suspicious = publicWidget.Widget.extend({
    selector: '.oe_login_form',
    events: {
        'click button[type="submit"]': '_onLogIn',
    },
    /**
     * Event handler for the login button click.
     * It overrides the default behavior of the login button click and adds additional functionality.
     * @param {Object} ev - The event object.
     */
    _onLogIn: async function (ev) {
        ev.preventDefault();
        var $login = this.$el.find('#login');
        var $password = this.$el.find('#password');
        var $otp = this.$el.find('#otp');
        var $is_trusted = this.$el.find('#is_trusted');
        var uuid = sessionStorage.getItem('uuid');
        var ip, user_location, time_zone;
        // Get the user's IP address using a third-party API
        await $.getJSON('https://api.ipify.org?format=json', (data) => {
            ip = data.ip;
        });
        // Get the user's location and time zone using another third-party API
        await $.getJSON(`https://ipapi.co/${ip}/json/`, (data) => {
            user_location = `${data.city}, ${data.region}, ${data.country_name}`;
            time_zone = `${data.timezone} (UTC${data.utc_offset})`;
        });
        if ($password.val() && $login.val()) {
            var vals = {
                login: $login.val(),
                password: $password.val(),
                otp: $otp.val() || false,
                is_trusted: $is_trusted.length > 0 ? $is_trusted[0].checked : false,
                uuid: uuid,
                platform: navigator.platform,
                browser: this.getBrowser(navigator.userAgent),
                ip_address: ip,
                location: user_location,
                timezone: time_zone,
                redirect: location.hash
            };
            if (!uuid && !$otp.val()) {
                await this.sendOtp(vals, $otp);
            } else if ($otp.val()) {
                await this.checkOtp(vals);
            } else if (uuid) {
                await this.checkUuid(vals);
            }
        } else if (!$login.val()) {
            $login.focus();
        } else if (!$password.val()) {
            $password.focus();
        }
    },
    /**
     * Method to send OTP (One-Time Password) to the user.
     * It adds the OTP field to the login form dynamically.
     * @param {Object} vals - The login values.
     * @param {Object} $otp - The OTP input field.
     */
    sendOtp: function (vals, $otp) {
        if (!$otp || $otp.length == 0) {
            if (!otpFieldAdded) {
                jsonrpc('/web/login/send_otp', { 'vals':vals }).then((result) => {
                    if (result) {
                        this.$el.find('.alert-danger').remove();
                        this.$el.find('.field-otp').remove();
                        this.$el.find('#is_trusted').parent().remove();
                        const otpDiv = document.createElement('div');
                        otpDiv.innerHTML = `<br><label for="otp">Otp</label><br><input type="password" placeholder="OTP" name="password" id="otp" class="form-control" required="required" maxlength="6"><br>`;
                        const checkboxDiv = document.createElement('div');
                        checkboxDiv.innerHTML = `<input type="checkbox" name="is_trusted" id="is_trusted">   <label for="is_trusted">Trust this browser?</label>`;
                        const passwordField = this.$el.find('#password');
                        otpFieldAdded = true;
                        passwordField[0].insertAdjacentElement('afterend', checkboxDiv);
                        passwordField[0].insertAdjacentElement('afterend', otpDiv);
                    } else {
                        this.$el.find('.alert-danger').remove();
                        this.$el.find('#password').after(`
                            <p class="alert alert-danger" role="alert">
                                Wrong Login/Password
                            </p>
                        `);
                    }
                });
            } else {
                this.$el.find('.alert-danger').remove();
                this.$el.find('#otp').after(`
                    <p class="alert alert-danger" role="alert">
                        Please enter the OTP
                    </p>
                `);
                this.$el.find('#otp').focus();
            }
        }
    },
    /**
     * Method to check the entered OTP.
     * @param {Object} vals - The login values.
     */
    checkOtp: function (vals) {
        jsonrpc('/web/login/check_otp', { 'vals': vals }).then((result) => {
            if (result.success) {
                if (vals.is_trusted) {
                    sessionStorage.setItem('uuid', result.uuid);
                }
                this.$el.find('.alert-danger').remove();
                location.href = result.redirect;
            } else {
                this.$el.find('.alert-danger').remove();
                this.$el.find('#otp').after(`
                    <p class="alert alert-danger" role="alert">
                        Wrong OTP
                    </p>
                `);
            }
        });
    },
    /**
     * Method to check the UUID (Universally Unique Identifier).
     * @param {Object} vals - The login values.
     */
    checkUuid: function (vals) {
        jsonrpc('/web/login/check_uuid',  { 'vals':vals }).then((result) => {
            if (result.success) {
                this.$el.find('.alert-danger').remove();
                location.href = result.redirect;
            } else {
                this.sendOtp(vals, false);
            }
        });
    },
    /**
     * Method to get the user's browser name from the user agent.
     * @param {string} userAgent - The user agent string.
     * @returns {string} The browser name.
     */
    getBrowser: function (userAgent) {
        var browserName;
        if (userAgent.match(/chrome|chromium|crios/i)) {
            browserName = "Google Chrome";
        } else if (userAgent.match(/firefox|fxios/i)) {
            browserName = "Mozilla Firefox";
        } else if (userAgent.match(/safari/i)) {
            browserName = "Safari";
        } else if (userAgent.match(/opr\//i)) {
            browserName = "Opera";
        } else if (userAgent.match(/edg/i)) {
            browserName = "Edge";
        } else {
            browserName = "Not Detected";
        }
        return browserName;
    }
});