odoo.define('website_gdpr_odoo.gdpr_portal_template', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var Template = PublicWidget.Widget.extend({
        selector: '.gdpr_portal_template',
        events: {
            'click ._actionDelete': '_actionModalCloseAndOpen',
            'click ._actionDownload': '_onClickActionDownload',
            'click ._actionReqDownload': '_onClickActionReqDownload',
            'click .gdpr-close-button': '_actionModalCloseAndOpen',
            'click .gdpr-modal-confirm': '_onClickActionDelete',
        },
        /**
         * Action to transfer data to create record type of delete
         */
         _onClickActionDelete: function(ev) {
            ajax.jsonRpc('/gdpr_management/confirm', 'call', {
                'user_id': session.user_id,
                'template_id': this.template_id,
                'type': 'delete'
            })
         },
        /**
        * For opening and closing the modal
        */
        _actionModalCloseAndOpen: function(ev) {
            this.template_id = Number(ev.currentTarget.getAttribute("id"))
            this.el.querySelector(".gdpr-modal").classList.toggle("gdpr-show-modal")
        },
        /**
         * Action to transfer data to create record type of download
         */
        _onClickActionDownload: function(ev) {
            ajax.jsonRpc('/gdpr_management/confirm', 'call', {
                'user_id': session.user_id,
                'template_id': Number(ev.currentTarget.getAttribute("id")),
                'type': 'download'
            })
        },
        /**
         * Action to open window of the content to download
         */
        _onClickActionReqDownload: function(ev) {
            var req_id = Number(ev.currentTarget.getAttribute("id"))
            rpc.query({
                model: 'gdpr.request',
                method: 'action_download_pdf',
                args: [, req_id],
            }).then(function(result) {
                window.open(result['url'])
            });
        }
    })
    PublicWidget.registry.gdpr_portal_template = Template;
    return Template;
})
