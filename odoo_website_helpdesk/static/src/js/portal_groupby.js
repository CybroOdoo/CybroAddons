odoo.define("odoo_website_helpdesk.portal_group_by", function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;

    $("#group_select").on('change', function () {
    var search_value = $("#group_select").val();
    ajax.jsonRpc('/ticketgroupby', 'call', {
                'search_value': search_value,
            }).then(function(result) {
                $('.search_ticket').html(result);
                });
    })

})