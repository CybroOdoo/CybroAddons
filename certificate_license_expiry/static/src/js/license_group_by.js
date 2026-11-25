/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.licenseGroup = publicWidget.Widget.extend({

    selector: '.search_group_by_license',
    events: {
        'change #group_select_license': '_onChangeLicense'

    },
    //    This is for getting group value of license
    _onChangeLicense: function() {
        let self = this
        var search_value = self.$el.find("#group_select_license").val();
        if(search_value !== "0"){
            rpc('/licensegroupby', {
                'search_value': search_value,
            }).then(function(result) {
                self.__parentedParent.$el.find(".search_license").html(result);
            });
        }
    }
})