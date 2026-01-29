/** @odoo-module **/
import { patch } from 'web.utils';
import { Follower } from '@mail/components/follower/follower';
const message_list = [];
patch(Follower.prototype, 'odoo_advanced_chatter/static/src/js/schedule_mail.js', {
    // Method to handle the checkbox click event
    Check(event) {
        const followerId = this.follower.partner.id;
        const index = message_list.indexOf(followerId);
        if (index !== -1) {
            message_list.splice(index, 1);
        } else {
            message_list.push(followerId);
        }
        const shouldBeChecked = message_list.length > 0;
        this.follower.followedThread.composer.check = shouldBeChecked ? message_list.slice() : false;
    }
});
