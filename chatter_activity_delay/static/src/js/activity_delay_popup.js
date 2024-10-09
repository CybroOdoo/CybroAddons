/** @odoo-module **/
import { ActivityMarkAsDone } from "@mail/core/web/activity_markasdone_popover";
import { patch } from "@web/core/utils/patch";
import { Thread } from "@mail/core/common/thread_model";

patch(ActivityMarkAsDone.prototype,{
    async onClickDone() {
        // ------- If the Activity is done after the Due Date , its Scheduled date and Done Date is Shown in the Chatter---------
        const state = this.props.activity.state;
        const scheduledDate = this.props.activity.date_deadline;
        const doneDate = new Date().toJSON().slice(0, 10);
        const { res_id, res_model } = this.props.activity;
        const formattedDate = new Date(
            scheduledDate.year,
            scheduledDate.month - 1,
            scheduledDate.day,
            scheduledDate.hour,
            scheduledDate.minute,
            scheduledDate.second,
            scheduledDate.millisecond
        );
        const dueDate = formattedDate.toISOString().slice(0, 10);
        const thread = this.env.services['mail.store'].Thread.insert({
            id: res_id,
            model: res_model
        });
        if (state === 'overdue'){
            if( this.props.activity.feedback != undefined){
                this.props.activity.feedback = this.props.activity.feedback
                + "\n" + "DELAYED" + "\n" + "Due Date :" + dueDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
            else{
                this.props.activity.feedback = "DELAYED" + "\n" + "Due Date :" + dueDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
        }
        await this.props.activity.markAsDone();
        if (this.props.reload) {
            this.props.reload(thread, ["activities"]);
        }
        await thread.fetchNewMessages();
    },

    async onClickDoneAndScheduleNext() {
    //  ------- If the 'Done and Schedule Next' button is clicked for an activity after the due date, the scheduled date and done date are displayed in the chatter---------
        const { res_id, res_model } = this.props.activity;
        const thread = this.env.services['mail.store'].Thread.insert({
            id: res_id,
            model: res_model
        });
        if (this.props.onClickDoneAndScheduleNext) {
            this.props.onClickDoneAndScheduleNext();
        }
        if (this.props.close) {
            this.props.close();
        }
        const state = this.props.activity.state;
        const scheduledDate = this.props.activity.date_deadline;
        const doneDate = new Date().toJSON().slice(0, 10);
        const formattedDate = new Date(
            scheduledDate.year,
            scheduledDate.month - 1,
            scheduledDate.day,
            scheduledDate.hour,
            scheduledDate.minute,
            scheduledDate.second,
            scheduledDate.millisecond
        );
        const dueDate = formattedDate.toISOString().slice(0, 10);
        console.log('due', dueDate)
        if (state === 'overdue'){
            if( this.props.activity.feedback != undefined){
                this.props.activity.feedback = this.props.activity.feedback
                + "\n" + "DELAYED" + "\n" + "Due Date :" + dueDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
            else{
                this.props.activity.feedback = "DELAYED" + "\n" + "Due Date: " + dueDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
        }
        const action = await this.props.activity.markAsDoneAndScheduleNext();
        await thread.fetchNewMessages();
        this.thread?.fetchNewMessages();
        if (this.props.reload) {
            this.props.reload(thread, ["activities", "attachments"]);
        }
        if (!action) {
            return;
        }
        await new Promise((resolve) => {
            this.env.services.action.doAction(action, {
                onClose: resolve,
            });
        });
        if (this.props.reload) {
            this.props.reload(thread, ["activities"]);
        }
    }
})