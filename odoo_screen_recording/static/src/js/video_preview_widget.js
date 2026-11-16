/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useProps } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
//video widget
class videoWidget extends Component {
    static template = 'VideoWidget'
    props = useProps({
        ...standardFieldProps,
    });
    get videoSource() {
        return this.props.record.data[this.props.name] || false;
    }
}
export const VideoWidget = {
    component: videoWidget
}
registry.category("fields").add("videoWidget", VideoWidget);
