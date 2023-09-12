odoo.define('website_signup_approval.signup', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var MySignUpForm = publicWidget.registry.SignUpForm.extend({
        _onSubmit: function (el) {
        /**
        *Override onSubmit function for sending approval request
        */
        var file = this.$('.get_attach');
        var email = this.$('input[name=login]').val();
        var username = this.$('input[name=name]').val();
        var password = this.$('input[name=password]').val();
        //Get signup information's from user
        const data_array = []
        var count=0;
        for (var doc = 0; doc < file.length; doc++) {
              var SelectedFile = new FileReader();
              var data = SelectedFile.readAsDataURL(file[doc].files[0]);
              SelectedFile.addEventListener('load', (e) => {
                 count++;
                 const data = e.target.result;
                 data_array.push(data)
                 if (count===(file.length)){
                 //Pass parameters to the route
                    this._rpc({
                      route: '/web/signup/approve',
                      params: {
                          'data':data_array,
                          'email':email,
                          'username':username,
                          'password':password
                      },
                    });
                 }
              });
            }
        },
    });
    publicWidget.registry.MySignUpForm = MySignUpForm;
    return MySignUpForm;
});
