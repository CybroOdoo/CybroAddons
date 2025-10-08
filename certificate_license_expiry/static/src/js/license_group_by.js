odoo.define("certificate_license_expiry.portal_license_group_by", function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var registry = require("@web/core/registry")
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var Template = publicWidget.Widget.extend({
    selector: '.search_group_by_license',
    events : {
        'change #group_select_license' : '_onChangeLicense'
    },
//    This is for getting group value of certificates
    _onChangeLicense: function(){
        let self = this
        var search_value = self.$el.find("#group_select_license").val();
        ajax.jsonRpc('/licensegroupby', 'call', {
            'search_value': search_value,
        }).then(function(result) {
            self.__parentedParent.$el.find(".search_license").html(result);
            });
    }
})
publicWidget.registry.search_group_by_license_group = Template;
return Template
})
