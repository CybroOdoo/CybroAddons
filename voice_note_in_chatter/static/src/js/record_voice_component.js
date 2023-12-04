/** @odoo-module **/
import { registerMessagingComponent } from '@mail/utils/messaging_component';
const { Component } = owl;

export class AttachmentAudio extends Component {
    /**
     * @returns {AttachmentAudio}
     */
    get attachmentAudio() {
        return this.props.record;
    }
}
Object.assign(AttachmentAudio, {
    props: { record: Object },
    template: 'web.AttachmentAudioField',
});
registerMessagingComponent(AttachmentAudio);
