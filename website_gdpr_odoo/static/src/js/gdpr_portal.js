/** @odoo-module */

import publicWidget from '@web/legacy/js/public/public_widget';
import {session} from "@web/session";
import { jsonrpc } from "@web/core/network/rpc_service";


var Template = publicWidget.Widget.extend({
    selector: '.gdpr_portal_template',
    events: {
        'click ._actionDelete': '_actionModalCloseAndOpen',
        'click ._actionDownload': '_onClickActionDownload',
        'click ._actionReqDownload': '_onClickActionReqDownload',
        'click .gdpr-close-button': '_actionModalCloseAndOpen',
        'click .gdpr-modal-confirm': '_onClickActionDelete',
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    /**
     * Action to transfer data to create record type of delete
     */
     _onClickActionDelete: function(ev) {
        jsonrpc('/gdpr_management/confirm',{
            user_id: session.user_id,
            template_id: this.template_id,
            type: 'delete'
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
        jsonrpc('/gdpr_management/confirm',{
            user_id: session.user_id,
            template_id: Number(ev.currentTarget.getAttribute("id")),
            type: 'download'
        })
    },
    /**
     * Action to open window of the content to download
     */
    _onClickActionReqDownload: function(ev) {
        var req_id = Number(ev.currentTarget.getAttribute("id"))
        this.orm.call('gdpr.request', 'action_download_pdf',[,req_id],{}
        ).then(function(result) {
            window.open(result['url'])
        });
    }
})
publicWidget.registry.gdpr_portal_template = Template;
return Template;
