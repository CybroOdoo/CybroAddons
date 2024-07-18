/* @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { sprintf } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";
import { loadWysiwygFromTextarea } from "@web_editor/js/frontend/loadWysiwygFromTextarea";
console.log('LLLLLLLLLLLLLLLLL')
publicWidget.registry.subscriptionDetail = publicWidget.Widget.extend({
    selector: '.subscription_detail_temp',
    events: {
        'click .btnShowCloseSubscriptionModal': '_onClickShowModal',
        'click .close_modal': '_onClickCloseModal',
    },
    /**
     *open modal to apply close reason
     */
    _onClickShowModal: function () {
        this.el.querySelector('#subscription_close_modal').style.display = 'block';
    },
    /**
     *close the document modal
     */
    _onClickCloseModal: function () {
        this.el.querySelector('#subscription_close_modal').style.display = 'none';
    },

    });