/** @odoo-module */
import {ActivityMarkDonePopover} from '@mail/components/activity_mark_done_popover/activity_mark_done_popover';
import { patch } from 'web.utils';
var core = require('web.core');
var _t = core._t;
patch(ActivityMarkDonePopover.prototype,'chatter_activity_delay/static/src/js/activity_delay_popup.js', {
         setup() {
           this._super.apply(this, arguments);
         },
         async _onClickDone() {
            const state = this.activity.state;
            const scheduledDate = this.activity.dateDeadline;
            const doneDate = new Date().toJSON().slice(0, 10);
            const chatter = this.activityViewOwner && this.activityViewOwner.activityBoxView.chatter;
            const webRecord = this.webRecord;
            const thread = this.activity.thread;

            if (state === 'overdue') {
                await this.activity.markAsDone({
                    feedback: state === 'overdue' ?
                     this._feedbackTextareaRef.el.value + "\n" +  "DELAYED" + "\n" + "  Due Date:  " + scheduledDate + "\n" + "Activity Done Date:  " + doneDate :
                                    this.feedbackTextareaRef.el.value
                });
                if (chatter && chatter.exists() && chatter.component) {
                    chatter.reloadParentView();
                }
                if (webRecord) {
                    webRecord.model.load({ resId: thread.id });
                }
            }
            else {
                this._super.apply(this, arguments);
            }
         },
})
