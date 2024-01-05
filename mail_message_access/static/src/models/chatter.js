/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import { session } from '@web/session';
import { attr } from '@mail/model/model_field';

registerPatch({
    name : 'Chatter',
    /**
    * @returns
    * -Boolean: access values from the session.
    **/
    fields : {
        AllowSendMessageBtn: attr({
            default: session.access_send_message_btn
        }),
        AllowLogNoteBtn: attr({
            default: session.access_log_note_btn
        })
    }
})
