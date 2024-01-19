/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted , useState} from "@odoo/owl";
//video widget
class videoWidget extends Component {
    static template = 'VideoWidget'
    setup() {
        onMounted(this.mount);
        super.setup();
        this.state = useState({
           value:false
        });
    }
    mount() {
        $('source').attr('src', this.props.record.data[this.props.name]);
    }
}
export const VideoWidget = {
    component: videoWidget
}
registry.category("fields").add("videoWidget", VideoWidget);
