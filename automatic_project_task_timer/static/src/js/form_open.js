/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { StatusBarField } from "@web/views/fields/statusbar/statusbar_field";
import { useService } from "@web/core/utils/hooks";

patch(FormRenderer.prototype, {
    // Patched the form renderer to show the notification for already existing task.
    setup() {
        super.setup();
        this.notification = useService("notification");
        if (this.props?.record?.resModel === "project.task" && this.props.record?.data?.is_status_stage) {
            this.notification.add(
                "The timer will not work properly for existing tasks until the stage is updated. Please change the stage once to activate the timer.",
                { title: "Warning", type: "warning" }
            );
        }
    },
});

patch(StatusBarField.prototype, {
    // Immediately save task record when stage is changed in the status bar
    async selectItem(item) {
        await super.selectItem(...arguments);
        if (this.props.record?.resModel === "project.task" && this.props.name === "stage_id") {
            await this.props.record.save();
        }
    },
});

