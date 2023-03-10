/** @odoo-module **/

import { registerModel } from '@mail/model/model_core';
import { attr, one } from '@mail/model/model_field';
import { clear } from '@mail/model/model_field_command';
import { isEventHandled, markEventHandled } from '@mail/utils/utils';

registerModel({
    name: 'AttachmentAudio',
    recordMethods: {
    },
    fields: {
        /**
         * Determines the attachment of this Audio.
         */
        attachment: one('Attachment', {
            identifying: true,
        }),
        /**
         * States the attachmentList displaying this Attachment audio.
         */
        attachmentList: one('AttachmentList', {
            identifying: true,
            inverse: 'attachmentAudio',
        }),
        /**
         * Download Audio Attachment.
         */
        downloadUrl: attr({
            related:'attachment.downloadUrl'
        }),
    },
});