/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.certificateSearch = publicWidget.Widget.extend({
    selector: '.search_group_by_certificates',
    events: {
        'click #search_certificates': '_onClickCertificates',
        'input #certificates_search_box': '_onInputCertificates',
    },
    //    This is for getting search value of certificates
    _onClickCertificates: function () {
        let self = this;
        var search_value = self.$el.find("#certificates_search_box").val();
        if (!search_value.trim()) {
            window.location.href = '/my/certificates';
            return;
        }
        rpc('/certificatesearch', {
            'search_value': search_value,
        }).then(function (result) {
            self.__parentedParent.$el.find(".search_certificates").html(result);
        });
    },
    //    This reloads all records when search box is cleared
    _onInputCertificates: function () {
        var search_value = this.$el.find("#certificates_search_box").val();
        if (!search_value.trim()) {
            window.location.href = '/my/certificates';
        }
    },
})
