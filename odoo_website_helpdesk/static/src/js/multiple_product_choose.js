odoo.define('odoo_website_helpdesk.multiple_product_choose', function(require) {
    "use strict";
    var ajax = require('web.ajax');
    $(document).ready(function() {
         ajax.rpc('/product').then(function (res) {
            var ar = res
            $('#product').empty()
            $(ar).each(function(i){
            $('#product').append("<option value=" + ar[i].id + ">" + ar[i].name + "</option>");
            });
            $('#product').SumoSelect({ clearAll: true });
        });
  });
});