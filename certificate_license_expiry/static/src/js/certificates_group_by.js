odoo.define("certificate_license_expiry.portal_certificates_group_by", function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var registry = require("@web/core/registry")
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var Template = publicWidget.Widget.extend({
    selector: '.search_group_by_certificates',
    events : {
        'click #group_select_certificates' : '_onChangeCertificates'
    },
//    This is for getting group value of certificates
    _onChangeCertificates: function(){
        let self = this
        var search_value = self.$el.find("#group_select_certificates").val();
        ajax.jsonRpc('/certificatesgroupby', 'call', {
            'search_value': search_value,
        }).then(function(result) {
            self.__parentedParent.$el.find(".search_certificates").html(result);
            });
    }
})
publicWidget.registry.search_group_by_certificates_group = Template;
return Template
})
