/**
     * This file is used to give a success alert after requesting a call for price.
*/

odoo.define('website_call_for_price.create', function (require) {
"use strict";
    const rpc = require('web.rpc');
    var core = require('web.core');

    $('#send_btn').on('click', function(){
          var first = $('#first_name').val();
          var last = $('#last_name').val();
          var product_id = $('#product_id').val();
          var phone = $('#phone').val();
          var email = $('#email').val();
          var message = $('#message').val();
          var qty = $('#quantity').val();
          rpc.query({
                model: "call.price",
                method: "create_form",
                args:[first,last,product_id,phone,email,message,qty]
                }).then(function (result) {
                    document.getElementById('alert_message').style.display = "block"
                });
    });
});