/* @odoo-module */
import { AttachmentList } from "@mail/core/common/attachment_list";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { useState } from "@odoo/owl";
const ImageActions = AttachmentList.components.ImageActions;

const customImage = {
    setup(){
        super.setup();
        this.state = useState({
            isPublicUser : user.userId === null
        });
    }
};
patch(AttachmentList.prototype, customImage);