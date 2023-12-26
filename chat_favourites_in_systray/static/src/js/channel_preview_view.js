/** @odoo-module **/

import { ChannelPreviewView } from '@mail/components/channel_preview_view/channel_preview_view';
import { registerPatch } from "@mail/model/model_core";
import { patch } from 'web.utils';
const components = { ChannelPreviewView };
const ajax = require('web.ajax');
const rpc = require('web.rpc');
const { session } = require('@web/session');

//Channel preview is patched to extend click and add view of star function
registerPatch({
    name:'ChannelPreviewView',
    lifecycleHooks: {
        _created() {
            this.willStart()
        },
    },
    recordMethods: {
        /**
         * @Override
         */
         onClick(ev){
            if (event.target.id.startsWith('star_icon_')) {
            //Returns if the id starts with 'star_icon_'
                return;
            }
            return this._super(...arguments);
         },
         async willStart(){
            const domain = [['id', '=', session.uid]];
            const fields = ['mail_channel_ids'];
            this.thread.favour_btn = false;
            await rpc.query({
                args: [domain, fields],
                method: 'search_read',
                model: 'res.users',
            }).then((data) => {
                this.thread.is_favour = data[0].mail_channel_ids.includes(this.thread.id) ? true : false;
            });
         },
    },
});
/*
Star click function is defined here, when clicked on the star, based on
previous state the chat will be selected or deselected as favourite
*/
patch( components.ChannelPreviewView.prototype, 'chat_favourites_in_systray', {
       _onClickMarkFavourite(ev){
        let thread = this.props.record.thread
        let star = this.root.el.querySelector('#star_icon_' + thread.id)
        if (star.classList.contains('text-danger')) {
            star.classList.remove('text-danger');
            star.classList.add('text-muted');
             ajax.jsonRpc('/disable_favourite', 'call', {
                active_id : thread.id,
                kwargs : {user_id :session.uid}
            }).then((data) => {
                thread.is_favour = false;
                this.messaging.models['Thread'].performRpcChannelInfo({
                    ids: [thread.id]
                });
            });
        }
        else {
            star.classList.remove('text-muted');
            star.classList.add("text-danger");
            ajax.jsonRpc('/enable_favourite', 'call', {
                active_id : thread.id,
                kwargs : {user_id :session.uid}
            }).then((data) => {
                thread.is_favour = true;
                this.messaging.models['Thread'].performRpcChannelInfo({
                    ids: [thread.id]
                });
            });
        }
    }
});
