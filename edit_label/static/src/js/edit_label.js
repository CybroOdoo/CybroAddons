/** @odoo-module */
import { FormLabel } from "@web/views/form/form_label";
import { patch } from '@web/core/utils/patch';
import { jsonrpc } from "@web/core/network/rpc_service";

patch(FormLabel.prototype, {
    /**
     * Overrides the behavior on double-click event for the FormLabel component.
     * Enables inline editing of labels based on user permissions.
     * @override
     */
    async onDblClick(ev) {
        this.access = false
        var self = this;
        jsonrpc(`/web/dataset/call_kw/res.users/login_user`, {
            model: 'res.users',
            method: 'login_user',
            args: [],
            kwargs: {},
        }).then(function(result) {
            if (result === true) {
                self.field_name = ''
                var $label = $(ev.target);
                self.label = $label;
                self.field_name = $label[0].innerText;
                if ($label[0].localName === 'label') {
                    var value = $($label).replaceWith(`<input id="label_edit" class="edit_label" data-label_for="${$(ev.target)[0].attributes.for.nodeValue}" value='${self.field_name}'>${$(self).text()}</input>`);
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
        var inputValue = $('.edit_label').val();
        var label_for = $(event.target).data('label_for');
        var field_tech_name = this.props.fieldName;
        var inputFieldName;
        var ids = this.idsForLabels
        if (this.label[0].htmlFor) {
            var inputFieldName = this.label[0].htmlFor
            var inputFieldLabel = this.field_name
        }
        jsonrpc(`/web/dataset/call_kw/ir.ui.view/edit_xml_field_label`, {
            model: 'ir.ui.view',
            method: 'edit_xml_field_label',
            args: [ModelName, ViewType, inputField, inputFieldName, inputValue, field_tech_name],
            kwargs: {}
        }).then(function(result) {
            if (result === true) {
                self.label[0].innerText = inputValue;
                $('.edit_label').replaceWith(self.label);
                location.reload();
            } else {
                console.error("Cant be edited")
            }
        });
    }
});
