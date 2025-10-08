odoo.define('user_password_strength.reset_user', function (require) {
    "use strict";

    var PublicWidget = require('web.public.widget');
    var ajax = require("web.ajax");

    var ResetForm = PublicWidget.Widget.extend({
        selector: '.oe_website_login_container',
        events: {
            'input input[type="password"]': '_onPasswordInput',
        },

        _onPasswordInput: function () {
            var passwordField = document.getElementById("password");
            var confirmPasswordField = document.getElementById("confirm_password");

            // Call function to update password strength progress for both password and confirm password fields
            this._updateProgress(passwordField);
            this._updateProgress(confirmPasswordField);
        },

        _updateProgress: function (passwordField) {
            var current_pwd = passwordField ? passwordField.value : "";

            // Reset if password length is zero
            if (current_pwd.length === 0) {
                var progressBar = document.getElementById("progress");
                if (progressBar) {
                    progressBar.value = "0";
                    progressBar.style.backgroundColor = "#FF0000"; // Red for no input
                }
                return;
            }

            // AJAX call to get configuration settings
            ajax.jsonRpc('/web/config_params', 'call', {}).then(function (data) {
                var list = [];
                for (let x in data) {
                    list.push(data[x]);
                }

                // Count the number of enabled password conditions
                var flag = 0;
                for (var i = 0; i < list.length; i++) {
                    if (list[i] === 'True') {
                        flag++;
                    }
                }
                // Check how many conditions the current password satisfies
                var prog = [/[$@$!%*#?&]/, /[A-Z]/, /[0-9]/, /[a-z]/]
                    .reduce((memo, test) => memo + test.test(current_pwd), 0);

                // Increase progress if password length is greater than 7 characters
                if (prog > 2 && current_pwd.length > 7) {
                    prog++;
                }

                var progress = "";
                var colors = ['#FF0000', '#00FF00', '#0000FF'];
                var currentColor = colors[0]; // Default to red

                // Update progress and color based on the number of conditions (flag)
                if (flag === 5) {
                    switch (prog) {
                        case 0:
                        case 1:
                            progress = "20";
                            currentColor = colors[0];
                            break;
                        case 2:
                            progress = "25";
                            currentColor = colors[0];
                            break;
                        case 3:
                            progress = "50";
                            currentColor = colors[1]; // Green
                            break;
                        case 4:
                            progress = "75";
                            currentColor = colors[1];
                            break;
                        case 5:
                            progress = "100";
                            currentColor = colors[1];
                            break;
                    }
                } else if (flag === 4) {
                    switch (prog) {
                        case 0:
                        case 1:
                        case 2:
                            progress = "25";
                            currentColor = colors[0];
                            break;
                        case 3:
                            progress = "50";
                            currentColor = colors[0];
                            break;
                        case 4:
                            progress = "75";
                            currentColor = colors[1];
                            break;
                        case 5:
                            progress = "100";
                            currentColor = colors[1];
                            break;
                    }
                } else if (flag === 3) {
                    switch (prog) {
                        case 0:
                        case 1:
                        case 2:
                        case 3:
                            progress = "33.33";
                            currentColor = colors[0];
                            break;
                        case 4:
                            progress = "66.66";
                            currentColor = colors[1];
                            break;
                        case 5:
                            progress = "100";
                            currentColor = colors[1];
                            break;
                    }
                } else if (flag === 2) {
                    if (prog !== 5) {
                        progress = "50";
                        currentColor = colors[0];
                    } else {
                        progress = "100";
                        currentColor = colors[1];
                    }
                } else if (flag === 1) {
                    progress = "100";
                    currentColor = colors[1]; // Green for fully satisfied
                }
                // Update the progress bar
                var progressBar = document.getElementById("progress");
                if (progressBar) {
                    progressBar.value = progress;
                    progressBar.style.backgroundColor = currentColor;
                }
            });
        },
    });

    PublicWidget.registry.ResetForm = ResetForm;
    return ResetForm;
});
