odoo.define('whatsapp_product_inquiry.WebsiteSaleController', function (require) {
    "use strict";
    var ajax = require('web.ajax')
    function whatsappNumberValidator() {
        //Function for checking the company whatsapp number
        ajax.jsonRpc('/whatsapp_number/validator', 'call', {
        }).then(function(data){
            if (data==true) {
            //If whatsapp number added, Inquire button will be visible
                self.$("#whatsapp_inquiry_link").show();
            }
        });
    };
    whatsappNumberValidator();
});
