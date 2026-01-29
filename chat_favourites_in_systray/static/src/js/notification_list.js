/** @odoo-module **/

import { NotificationList } from '@mail/components/notification_list/notification_list';
import { patch } from 'web.utils';

const components = { NotificationList };
const ajax = require('web.ajax');
components.NotificationList._allowedFilters.push('livechat');

patch(components.NotificationList.prototype, 'chat_favourites_in_systray/static/src/js/notification_list.js', {

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Override to include favourite chats.
     *
     * @override
     */
    _getThreads(props) {
    if (this.__owl__.parent.favourite_button == true) {
        return this.messaging.models['mail.thread'].all(thread =>
                thread.model === 'mail.channel'&&
                thread.isChatChannel &&
                thread.is_favourite === true
            );
    }
    return this._super(...arguments);
    },
});
