/** @odoo-module **/
import { registry } from "@web/core/registry";
import {Component, onWillStart} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


const actionRegistry = registry.category("actions");
class MediaTypeDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService('orm')
        this.actionService = useService("action");
        onWillStart(async () => {
            this.result = await this.orm.call("media.asset", "get_media_type_data", [],{});
                });
  }


}
MediaTypeDashboard.template = "media_type_dashboard.MediaTypeDashboard";
actionRegistry.add("media_type_dashboard_tag", MediaTypeDashboard);