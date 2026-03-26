/** @odoo-module */
import { FormLabel } from "@web/views/form/form_label";
import { patch } from '@web/core/utils/patch';
import { rpc } from "@web/core/network/rpc";

patch(FormLabel.prototype, {
    /**
     * Overrides the behavior on double-click event for the FormLabel component.
     * Enables inline editing of labels based on user permissions.
     * @override
     */
    async onDblClick(ev) {
        this.access = false
        var self = this;
        rpc(`/web/dataset/call_kw/res.users/login_user`, {
            model: 'res.users',
            method: 'login_user',
            args: [],
            kwargs: {},
        }).then(function(result) {
            if (result === true) {
                var $label = ev.target;
                self.field_name = $label.innerText;
                if ($label.localName === 'label') {
                // create input element
                var input = document.createElement("INPUT");
                input.setAttribute("id", "label_edit");
                input.setAttribute("class", "edit_label");
                input.setAttribute("data-label_for", ev.target.attributes.for.nodeValue);
                input.value = self.field_name;
                self.label = $label;
                    var value = $label.replaceWith(input);
                    document.getElementById("label_edit").onblur = function() {
                        self.UpdateField(event)
                    };
                }
            }
        });
    },
    /**
     * Handles the label editing functionality on blur.
     * Updates label values based on user input and permissions.
     * @param {Event} event - The blur event triggered when editing ends.
     */
    UpdateField(event) {
        var self = this;
        var ModelName = this.props.record._config.resModel
        var ViewType = this.props.fieldInfo.viewType
        var inputField = this.field_name
        var inputValue = event.target.value
        var label_for = event.target.dataset.label_for;
        var field_tech_name = this.props.fieldName;
        var inputFieldName;
        var ids = this.idsForLabels
        if (this.label.htmlFor) {
            var inputFieldName = this.label.htmlFor
            var inputFieldLabel = this.field_name
        }
        rpc(`/web/dataset/call_kw/ir.ui.view/edit_xml_field_label`, {
            model: 'ir.ui.view',
            method: 'edit_xml_field_label',
            args: [ModelName, ViewType, inputField, inputFieldName, inputValue, field_tech_name],
            kwargs: {}
        }).then(function(result) {
            if (result === true) {
                self.label.innerText = inputValue;
                event.target.replaceWith(self.label);
                location.reload();
            } else {
                console.error("Cant be edited")
            }
        });
    }
});
