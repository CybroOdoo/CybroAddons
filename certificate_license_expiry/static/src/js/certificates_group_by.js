/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.certificateGroup = publicWidget.Widget.extend({

       selector: '.search_group_by_certificates',
       events : {
        'click #group_select_certificates' : '_onChangeCertificates'

      },
//    This is for getting group value of certificates
       _onChangeCertificates: function(){
        var self = this;
            var searchValue = self.$el.find("#group_select_certificates").val();
            jsonrpc('/certificatesgroupby', {
            'search_value': searchValue,
        }).then(function(result) {
            self.__parentedParent.$el.find(".search_certificates").html(result);
            });
        }
})