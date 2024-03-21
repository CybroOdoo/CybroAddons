/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
const message_list = []

registerPatch({
    name: 'FollowerView',
    recordMethods:{
        //---to manage the recipients to whom the message should sent
        Check(){
        var index = message_list.indexOf(this.follower.partner.id)
        if (message_list.includes(this.follower.partner.id)){
            message_list.splice(index, 1)
        }
        else{
            message_list.push(this.follower.partner.id)
        }
        this.follower.followedThread.composer.check = message_list
        }
    }
})