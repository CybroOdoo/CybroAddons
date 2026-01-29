/** @odoo-module **/
import { attr } from '@mail/model/model_field';
import { session } from '@web/session';
import { registerFieldPatchModel } from '@mail/model/model_core';

registerFieldPatchModel('mail.chatter', 'mail_message_access/static/src/models/chatter.js', {
   /**
    * @returns
    * -Boolean: access values from the session.
    **/
    AllowSendMessageBtn: attr({
        default: session.access_send_message_btn
    }),
    AllowLogNoteBtn: attr({
        default: session.access_log_note_btn
    })
});
