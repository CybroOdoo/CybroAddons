odoo.define("certificate_license_expiry.portal_my_certificates", function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var el = $(document);
    var Template = publicWidget.Widget.extend({
        selector: '.search_group_by_certificates',
        events : {
            'click #search_certificates' : '_onClickCertificates',
        },
    //    This is for getting search value of certificates
        _onClickCertificates: function(){
            let self = this
            var search_value = self.$el.find("#certificates_search_box").val();
            ajax.jsonRpc('/certificatesearch', 'call', {
                'search_value': search_value,
            }).then(function(result) {
                self.__parentedParent.$el.find(".search_certificates").html(result);
                });
        }
})
publicWidget.registry.search_group_by_certificates_search = Template;
return Template
})
