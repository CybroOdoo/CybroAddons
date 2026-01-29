/** @odoo-module **/

import { MessagingMenu } from  '@mail/components/messaging_menu/messaging_menu';

import { patch } from 'web.utils';

const components = { MessagingMenu };
const ajax = require('web.ajax');
let favourite_button = false;

patch(components.MessagingMenu.prototype, 'chat_favourites_in_systray/static/src/js/messaging_menu.js', {

    _onClickToggler(ev) {
        this.favourite_button = false;
        this.messagingMenu.update({ activeTabId: 'all' });
        return this._super(...arguments);
    },

   _onClickFavourite(ev) {
        this.favourite_button = true;
        favourite_button = true;
        this.messagingMenu.update({ activeTabId: 'chat' });
        this.messagingMenu.toggleOpen();
   }
});
