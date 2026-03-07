/** @odoo-module **/

/*Extending the public widget of the signup form for checking the user
password strength conditions on key up function of the password field in
the sign up form,Based on the conditions from configuration settings.*/
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SignUpFormKeyupChange = publicWidget.Widget.extend({
    selector: '.oe_website_login_container',
    events: {
        'input input[type="password"]': '_onPasswordInput', // Using input event instead of keypress
    },
    start() {
        this._super.apply(this, arguments);
        setTimeout(() => {
            console.log("Progress after delay:", document.getElementById("progress"));
        }, 1000);
    },

    _onPasswordInput: function (ev) {
        const pwd = ev.currentTarget.value;
        const progressBar = document.getElementById("progress");

        if (!progressBar) return;

        // Reset when empty
        if (!pwd || pwd.length === 0) {
            progressBar.value = "0";
            progressBar.style.backgroundColor = "#FF0000";
            return;
        }

        // Get config values
        rpc('/web/config_params', {}).then((data) => {

            // Config flags
            const useUpper = data.config_upper === "True";
            const useLower = data.config_lower === "True";
            const useDigit = data.config_digit === "True";
            const useSymbol = data.config_special_symbol === "True";
            const useLength = data.config_strength === "True"; // length rule

            // Count enabled rules
            let enabledRules = 0;
            if (useUpper) enabledRules++;
            if (useLower) enabledRules++;
            if (useDigit) enabledRules++;
            if (useSymbol) enabledRules++;

            // Count satisfied rules
            let score = 0;
            if (useUpper && /[A-Z]/.test(pwd)) score++;
            if (useLower && /[a-z]/.test(pwd)) score++;
            if (useDigit && /[0-9]/.test(pwd)) score++;
            if (useSymbol && /[$@$!%*#?&]/.test(pwd)) score++;

            // Add bonus only if length >= 8 AND length rule enabled
            // Length rule is enabled → always count it
            if (useLength) {
                enabledRules++;
                if (pwd.length >= 8) {
                    score++;
                }
            }
            // Calculate percentage
            // score / enabledRules = percentage completion of enabled rules
            let percent = Math.round((score / enabledRules) * 100);

            // Ensure minimum boundaries
            if (percent < 0) percent = 0;
            if (percent > 100) percent = 100;

            // Set progress and color
            progressBar.value = percent.toString();

            // Colors:
            // 0-40  weak     RED
            // 41-70 medium   ORANGE
            // 71-100 strong  GREEN
            let color;
            if (percent <= 40) color = "#FF0000";
            else if (percent <= 70) color = "#FFA500";
            else color = "#00CC00";

            progressBar.style.backgroundColor = color;
        });
    },
});
