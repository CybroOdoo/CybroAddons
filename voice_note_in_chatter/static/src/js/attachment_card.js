/** @odoo-module */
import {
    AttachmentCard
} from "@mail/components/attachment_card/attachment_card";
import {
    patch
} from "@web/core/utils/patch";

patch(AttachmentCard.prototype, "attachment_card", {
    /**
    * Play Audio Attachment.
    */
    onPlay(ev) {
        var audioElements = $('.o_attachment_audio');
        //Pause Audio When other Audio plays
        audioElements.each(function(index, element) {
            if (ev.target != element.children[0]) {
                for (let i = 0; i < element.children.length; i++) {
                    const childElement = element.children[i];
                    childElement.pause()
                }
            }
        });
    }
});
