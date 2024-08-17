odoo.define("certificate_license_expiry.portal_my_license", function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var el = $(document);
    var Template = publicWidget.Widget.extend({
        selector: '.search_group_by_license',
        events : {
            'click #search_license' : '_onClickLicense'
        },
    //    This is for getting search value of license
        _onClickLicense: function(){
            let self = this
            var search_value = self.$el.find("#license_search_box").val();
            ajax.jsonRpc('/licensesearch', 'call', {
                'search_value': search_value,
            }).then(function(result) {
                self.__parentedParent.$el.find(".search_license").html(result);
                });
        }
})
publicWidget.registry.search_group_by_license_search = Template;
return Template
})
