odoo.define("odoo_website_helpdesk.portal_group_by_and_search", function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    publicWidget.registry.portalSearchGroup = publicWidget.Widget.extend({
        selector: '.portal_group_by',
        events: {
            'change #group_select': '_onGroupSelectChange',
            'click #search_ticket': '_searchTickets',
        },
//        GroupBy filtering the portal tickets
        _onGroupSelectChange: function (ev) {
            var self = this;
            var searchValue = this.$el.find('#group_select').val();
            ajax.jsonRpc('/ticketgroupby', 'call', {
                'search_value': searchValue,
            }).then(function (result) {
                  $('.search_ticket').html(result);
            });
        },
//        Searching the portal tickets
        _searchTickets: function (ev) {
        var self = this;
        var search_value = this.$el.find("#search_box").val();
        ajax.jsonRpc('/ticketsearch', 'call', {
                'search_value': search_value,
            }).then(function(result) {
                var self = this;
                $('.search_ticket').html(result);
                });
        }
    });
})
