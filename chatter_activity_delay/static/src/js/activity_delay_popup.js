/** @odoo-module **/
import { ActivityMarkAsDone } from "@mail/core/web/activity_markasdone_popover";
import { patch } from "@web/core/utils/patch";

patch(ActivityMarkAsDone.prototype,{
    async onClickDone() {
//    ------- If the Activity is done after the Due Date , its Scheduled date and Done Date is Shown in the Chatter---------
        const state = this.props.activity.state;
        const scheduledDate = this.props.activity.date_deadline;
        const doneDate = new Date().toJSON().slice(0, 10);
        const { res_id, res_model } = this.props.activity;
        const thread = this.threadService.getThread(res_model, res_id);
        if (state === 'overdue'){
            if( this.props.activity.feedback != undefined){
                this.props.activity.feedback = this.props.activity.feedback
                + "\n" + "DELAYED" + "\n" + "Due Date :" + scheduledDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
            else{
                this.props.activity.feedback = "DELAYED" + "\n" + "Due Date :" + scheduledDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
        }
        await this.env.services["mail.activity"].markAsDone(this.props.activity);
        if (this.props.reload) {
            this.props.reload(thread, ["activities"]);
        }
        await this.threadService.fetchNewMessages(thread);
    },


    async onClickDoneAndScheduleNext() {
    //    ------- If the 'Done and Schedule Next' button is clicked for an activity after the due date, the scheduled date and done date are displayed in the chatter---------
        const { res_id, res_model } = this.props.activity;
        const thread = this.threadService.getThread(res_model, res_id);
        if (this.props.onClickDoneAndScheduleNext) {
            this.props.onClickDoneAndScheduleNext();
        }
        if (this.props.close) {
            this.props.close();
        }
        const state = this.props.activity.state;
        const scheduledDate = this.props.activity.date_deadline;
        const doneDate = new Date().toJSON().slice(0, 10);
        if (state === 'overdue'){
            if( this.props.activity.feedback != undefined){
                this.props.activity.feedback = this.props.activity.feedback
                + "\n" + "DELAYED" + "\n" + "Due Date :" + scheduledDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
            else{
                this.props.activity.feedback = "DELAYED" + "\n" + "Due Date :" + scheduledDate
                + "\n" + "Activity Done Date:  " + doneDate
            }
        }
        const action = await this.env.services["mail.activity"].markAsDoneAndScheduleNext(
            this.props.activity
        );
        this.threadService.fetchNewMessages(thread);
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
