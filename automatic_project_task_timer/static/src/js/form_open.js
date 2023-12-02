/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormRenderer } from '@web/views/form/form_renderer';
import { useService } from "@web/core/utils/hooks";
patch(FormRenderer.prototype, "warning", {
     // Patched the form render to show the notification for already existing task.
        setup(){
           this._super.apply();
           if(this.props.record.data.is_status_stage)
                {
                this.notification = useService("notification");
                this.notification.add("Timer will not works properly for already existing task, To make that, Change the stage once again after activating task timer from configuration.", {title: "Warning", type: "danger"});
                }
        },
});
