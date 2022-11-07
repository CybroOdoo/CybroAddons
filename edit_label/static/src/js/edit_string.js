/** @odoo-module */
import { formView } from "@web/views/form/form_view";
import { FormLabel } from "@web/views/form/form_label";
const { useState, Component } = owl;
const components = formView.Renderer.components;
import { ForecastedButtons } from "@stock/stock_forecasted/forecasted_buttons";
import { patch } from '@web/core/utils/patch';
var rpc = require('web.rpc');

const { onWillStart } = owl;

patch(FormLabel.prototype, 'edit_label.FormLabel',{
    setup() {
        this._super.apply();
    },

    async onDblClick(ev){
        this.access = false
        var self = this;
        rpc.query({
                model: 'res.users',
                method: 'login_user',
                args: [],
        }).then(function(result) {
            if(result === true){
                self.field_name = ''
                var $label = $(ev.target);
                self.label = $label;
                self.field_name = $label[0].innerText;
                if($label[0].localName === 'label'){
                    var value = $($label).replaceWith(`<input id="label_edit" class="edit_label" data-label_for="${$(ev.target)[0].attributes.for.nodeValue}" value='${self.field_name}'>${$(self).text()}</input>`);
                    document.getElementById("label_edit").onblur = function() {self.myFunction(event)};
                }
            }
        });

    },
     myFunction(event) {
            var self = this;
            var ModelName = this.props.record.resModel
            var ViewType = this.props.record.__viewType
            var inputField = this.field_name
            var inputValue = $('.edit_label').val();
            var label_for = $(event.target).data('label_for');
            var field_tech_name;
            var inputFieldName;
            var ids = this.idsForLabels
            if(this.label[0].htmlFor){
                var inputFieldName = this.label[0].htmlFor
                var inputFieldLabel = this.field_name
            }

            rpc.query({
                model: 'ir.ui.view',
                method: 'edit_xml_field_label',
                args: [ModelName, ViewType, inputField, inputFieldName, inputValue, field_tech_name],
            }).then(function(result) {
                if (result === true) {
                    self.label[0].innerText = inputValue;
                    $('.edit_label').replaceWith(self.label);
                    location.reload();
                }
                else{
                    console.log("Error")}

            });

     }
});
//export class FormLabelDouble extends FormLabel {
//    setup() {
//            super.setup();
//            useListener('double-click', this.onDblClick());
//            }
//    onDblClick() {
//        console.log('hai here')
//    }
//
//}
//FormLabelDouble.template = "edit_label.FormLabel";
//console.log(FormLabelDouble, "lll")