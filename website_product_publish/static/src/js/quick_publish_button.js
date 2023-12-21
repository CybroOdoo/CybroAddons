/** @odoo-module **/
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
const { Component, useState } = owl;
// Creating a new button widget for 'Quick Publish' which works same as the
//current publish button widget.
class QuickWebsitePublishButton extends Component{
 setup(){
    this.trueColor = "green"
    this.falseColor = "red"
    }
   updateValue(){
        this.props.update(!this.props.value)
   }
}
QuickWebsitePublishButton.template = "QuickWebsitePublishButton"
QuickWebsitePublishButton.props = {
 ...standardFieldProps,
 options: { type: Object, optional: true }
}
QuickWebsitePublishButton.supportedTypes = ["boolean"]
QuickWebsitePublishButton.extractProps = ({attrs}) => {
 return {options: attrs.options}
}
registry.category("fields").add("quick_publish_button", QuickWebsitePublishButton)
