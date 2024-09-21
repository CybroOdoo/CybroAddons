/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.certificateSearch = publicWidget.Widget.extend({
       selector: '.search_group_by_certificates',
       events : {
        'click #search_certificates' : '_onClickCertificates'

      },
      //    This is for getting search value of certificates
      _onClickCertificates: function(){
            let self = this
            var search_value = self.$el.find("#certificates_search_box").val();
            jsonrpc('/certificatesearch',{
                'search_value': search_value,
            }).then(function(result) {
                self.__parentedParent.$el.find(".search_certificates").html(result);
                });
            }
})