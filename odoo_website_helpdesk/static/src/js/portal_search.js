odoo.define("odoo_website_helpdesk.portal_search", function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;

    $("#search_ticket").on('click', function () {
    var search_value = $("#search_box").val();
    ajax.jsonRpc('/ticketsearch', 'call', {
                'search_value': search_value,
            }).then(function(result) {
                $('.search_ticket').html(result);
                });
    })

})