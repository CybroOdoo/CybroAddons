odoo.define('user_password_strength.signup_user', function (require) {
"use strict";
    // Extending the public widget of the signup form for checking the user
    // password strength conditions on key up function of the password field in
    // the sign up form,Based on the conditions from configuration settings.
    var PublicWidget = require('web.public.widget');
    var ajax = require("web.ajax");
    var password = document.getElementById("password");

    var MySignUpForm = PublicWidget.registry.SignUpForm.extend({
        selector: '.oe_signup_form',
        events: {
            'keyup': '_onKeyup',
        },
        _onKeyup: function () {
            // Rendering ajax Rpc call from controller through route
            ajax.jsonRpc('/web/config_params', 'call', {
            }).then(function (data) {
                var list=[]
                for (let x in data) {
                list.push(data[x]);
                }
                var flag = 0
                for(var i=0;i<=list.length;i++){
                    if(list[i] == 'True'){
                     flag +=1
                    }
                }
                var prog = [/[$@$!%*#?&]/, /[A-Z]/, /[0-9]/, /[a-z]/]
                        .reduce((memo, test) => memo + test.test(current_pwd),
                         0);
                if(prog > 2 && current_pwd.length > 7){
                    prog++;
                }
                var progress = "";
                var colors = ['#FF0000', '#00FF00','#0000FF'];
                var currentColor = 0;
                //When 5 conditions are enabled in config settings
                if (flag == 5){
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
                          currentColor = colors[1];
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
                }
                //When 4 conditions are enabled in config settings
                if (flag == 4){
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
                }
                //When 3 conditions are enabled in config settings
                if (flag == 3){
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
                }
                //When 2 conditions are enabled in config settings
                if (flag == 2) {
                    if (prog != 5) {
                        progress = "50";
                        currentColor = colors[0];
                    } else{
                        progress = "100";
                            currentColor = colors[1];
                    }
                }
                //When only 1 condition is enabled in config settings
                if (flag == 1){
                    progress = "100";
                    currentColor = colors[1];
                }
                var val = document.getElementById("progress")
                    if(val!== null){
                        document.getElementById("progress").value = progress;
                        document.getElementById("progress").style
                        .backgroundColor = currentColor;
                    }
                });
            // Reset if password length is zero
                var current_pwd = password.value
                if (current_pwd.length === 0) {
                document.getElementById("progress").value = "0";
                return;
                }
            },
    });

    PublicWidget.registry.MySignUpForm = MySignUpForm;
    return MySignUpForm;
});
