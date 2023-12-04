/** @odoo-module **/
import { registerNewModel } from '@mail/model/model_core';
import { attr, one2one } from '@mail/model/model_field';

function audio(dependencies) {
    class AttachmentAudio extends dependencies['mail.model'] {}

    AttachmentAudio.fields = {

        /**
         * Determines the attachment of this Audio.
         */
        attachment:one2one('mail.attachment', {
                inverse: 'attachment',
                readonly: true
        }),
        /**
         * Download Audio Attachment.
         */
        downloadUrl: attr({
            related:'attachment.downloadUrl'
        }),
    };
    AttachmentAudio.identifyingFields = ['attachment'];
    AttachmentAudio.modelName = 'mail.attachmentAudio';
    return AttachmentAudio;
}
registerNewModel('mail.attachmentAudio', audio);
