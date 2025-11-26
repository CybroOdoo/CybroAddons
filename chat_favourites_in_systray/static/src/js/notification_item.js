/** @odoo-module **/
import { NotificationItem } from "@mail/core/web/notification_item";
import { patch } from "@web/core/utils/patch";
import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from "@web/session";
import { useState } from "@odoo/owl";

patch(NotificationItem.prototype, {
    async setup() {
        super.setup();
        this.state = useState({
            thread: null,
            channels: [],
        });

        const thread = this.props?.slots?.icon?.__ctx?.thread;
        if (thread) {
            this.state.thread = thread;
        }

        // Fetch user's channel IDs
        const domain = [['id', '=', session.uid]];
        const fields = ['mail_channel_ids'];

        const data = await jsonrpc('/web/dataset/call_kw/res.users/search_read', {
            model: 'res.users',
            method: 'search_read',
            args: [domain, fields],
            kwargs: {},
        });

        this.state.channels = data[0]?.mail_channel_ids || [];
        // Set thread as favourite if it's in user's channels
        if (this.state.thread) {
            this.state.thread.favourite = this.state.channels.includes(this.state.thread.id);
        }
    },

    async _onClickMarkFavourite(ev) {
        const thread = this.props.slots.icon.__ctx.thread;
        const starClassList = ev.target.classList;

        if (starClassList.contains('text-danger')) {
            // Unmark as favourite
            starClassList.remove('text-danger');
            starClassList.add('text-muted');

            await jsonrpc('/disable_favourite', {
                active_id: thread.id,
                user_id: session.uid,
            });

            thread.favourite = false;
        } else {
            // Mark as favourite
            starClassList.add('text-danger');
            starClassList.remove('text-muted');

            await jsonrpc('/enable_favourite', {
                active_id: thread.id,
                user_id: session.uid,
            });

            thread.favourite = true;
        }
    },
});
