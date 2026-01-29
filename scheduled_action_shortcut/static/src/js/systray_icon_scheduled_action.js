/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ScheduledActionsTemplate } from './scheduled_actions';
const { mount, useExternalListener } = owl;
/**
 * ScheduledActions component for managing scheduled actions in the systray.
 */
class ScheduledActions extends owl.Component {
    setup() {
        this.action = useService("action");
    }
    setDropDown(event) {
        this.schedule_dropdown = event
    }
    //    This function will call at the time of clicking the systray icon
    _onClickScheduledAction() {
        var self = this;
        if (!this.schedule_dropdown) {
            this.schedule_dropdown = mount(ScheduledActionsTemplate, {
                target: document.body,
                props: {
                    setDropDown: this.setDropDown.bind(this)
                },
                env: this.env,
            })
        } else if (this.schedule_dropdown) {
            this.schedule_dropdown.then((res) => {
                this.env.bus.trigger("closeAllEvent:SA")
                delete self.schedule_dropdown
            })
        }
    }
}
ScheduledActions.template = "stick_scheduled_action.ScheduledActionSystray";
export const systrayItem = {
    Component: ScheduledActions
};
registry.category("systray")
    .add("ScheduledActions", systrayItem, {
        sequence: 1
    });
