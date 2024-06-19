/** @odoo-module **/

import { registerPatch } from '@mail/model/model_core';
import core from 'web.core';
import { useService } from "@web/core/utils/hooks";
import { attr, one } from '@mail/model/model_field';
import { clear, insert, link } from '@mail/model/model_field_command';
import { makeDeferred } from '@mail/utils/deferred';

registerPatch({
    name: 'ActivityMarkDonePopoverContentView',
    recordMethods: {
        async onClickDone() {
            //------- If the Activity is done after the Due Date , its Scheduled date and Done Date is Shown in the Chatter---------
            const state = this.activity.state;
            const scheduledDate = this.activity.dateDeadline;
            const doneDate = new Date().toJSON().slice(0, 10);
            const chatter = this.activityViewOwner && this.activityViewOwner.activityBoxView.chatter;
            const webRecord = this.webRecord;
            const thread = this.activity.thread;

            await this.activity.markAsDone({
                feedback: state === 'overdue' ?
                 this.feedbackTextareaRef.el.value + "\n" +  "DELAYED" + "\n" + "  Due Date:  " + scheduledDate + "\n" + "Activity Done Date:  " + doneDate :
                                this.feedbackTextareaRef.el.value
            });
            if (chatter && chatter.exists() && chatter.component) {
                chatter.reloadParentView();
            }
            if (webRecord) {
                webRecord.model.load({ resId: thread.id });
            }
        }
    }
});
