/** @odoo-module **/
import { registerPatch } from "@mail/model/model_core";

registerPatch({
    name: 'NotificationListView',
    fields:{
        filteredChannels:{
            compute() {
                if (this.filter === 'favourite') {
                        // "Favourite" filter is for favourite chats
                        return this.messaging.models['Channel']
                            .all(channel => channel.thread.isPinned && channel.thread.is_favour)
                            .sort((c1, c2) => c1.displayName < c2.displayName ? -1 : 1);
                }
                return this._super();
            }
        }
    }
});
