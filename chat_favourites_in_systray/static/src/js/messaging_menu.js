/** @odoo-module **/

import { MessagingMenu } from  '@mail/components/messaging_menu/messaging_menu';
import { registerPatch } from "@mail/model/model_core";
import { patch } from 'web.utils';
const components = { MessagingMenu };
const ajax = require('web.ajax');

registerPatch({
    /*
     MessagingMenu is patched using registerPatch to add the
     activeTabId as 'all' when clicked on regular chat icon
     */
    name: 'MessagingMenu',
    recordMethods: {
        onClickToggler(ev) {
            this._super(...arguments);
            this.messaging.messagingMenu.update({ activeTabId: 'all' });
        },
    },
});

patch( components.MessagingMenu.prototype,'chat_favourites_in_systray',{
    // MessagingMenu is patched to extend its functionalities
    _onClickFavourite(){
        // Click on star icon in the systray is handled by this function
        this.favourite_button = true;
        this.messagingMenu.update({ activeTabId: 'favourite' });
        this.messagingMenu.toggleOpen();
    },
    _onClickDesktopTabButton(ev){
        //ActiveTabId is updated
        this.messagingMenu.update({ activeTabId: ev.currentTarget.dataset.tabId });
    },
});
