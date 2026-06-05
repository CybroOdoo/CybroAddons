/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.licenseSearch = publicWidget.Widget.extend({
       selector: '.search_group_by_license',
       events : {
        'click #search_license' : '_onClickLicense'
      },
      //    This is for getting search value of license
     _onClickLicense: function(){
            let self = this
            var search_value = self.$el.find("#license_search_box").val();
            rpc('/licensesearch',{
                'search_value': search_value,
            }).then(function(result) {
                self.__parentedParent.$el.find(".search_license").html(result);
                });
            }
})
