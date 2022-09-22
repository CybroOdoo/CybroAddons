/** @odoo-module **/

import { ThreadPreview } from '@mail/components/thread_preview/thread_preview';

import { patch } from 'web.utils';

const components = { ThreadPreview };
const ajax = require('web.ajax');

patch(components.ThreadPreview.prototype, 'chat_favourites_in_systray/static/src/js/thread_preview.js', {

    async willStart() {
        const domain = [['id', '=', this.thread.id]];
        const fields = ['is_favourite'];
        const configs = await this.rpc({
            args: [domain, fields],
            method: 'search_read',
            model: 'mail.channel',
        });
        if (this.__owl__.parent.__owl__.parent.favourite_button){
            this.thread.favour_btn = true;
        }
        else{
            this.thread.favour_btn = false;
        }
        this.thread.is_favour = configs[0].is_favourite
    },

   _onClickMarkFavourite(ev) {
        var self = this;
        this.thread.starred = false;
        ajax.jsonRpc('mark_is_favourite', 'call', {
            'model':'mail.channel',
            'active_id': this.thread.id,
            }).then(function(result){
               var star = document.getElementById('star_icon_' + result)
               if($(star).hasClass('text-danger')){
                     $(star).removeClass('text-danger');
                     $(star).addClass('text-muted');
                     ajax.jsonRpc('/disable_favourite', 'call', {
                        model: 'mail.channel',
                        activate: false,
                        active_id : self.thread.id
                    }).then(function (data) {
                        self.thread.is_favour = false;
                        self.messaging.models['mail.thread'].performRpcChannelInfo({ ids: [self.thread.id] })
                    });
               } else {
                    $(star).removeClass('text-muted');
                    $(star).addClass("text-danger");
                    ajax.jsonRpc('/enable_favourite', 'call', {
                        model: 'mail.channel',
                        activate: true,
                        active_id : self.thread.id
                    }).then(function (data) {
                        self.thread.is_favour = true;
                        self.messaging.models['mail.thread'].performRpcChannelInfo({ ids: [self.thread.id] })
                    });
               }
           })
   }
});