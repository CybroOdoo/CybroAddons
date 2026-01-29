odoo.define('Edit_label.EditString', function(require) {
    "use strict";

    var FormRenderer = require('web.FormRenderer');
    var rpc = require('web.rpc');
    const ajax = require('web.ajax');


    FormRenderer.include({
        events: _.extend({}, FormRenderer.prototype.events, {
            'dblclick': '_onFormviewDblClick',
            'blur .edit_label': '_onBlur'
        }),
        label: '',
        _onFormviewDblClick: function(ev) {
            this.access = false
            var self = this
            rpc.query({
                model: 'res.users',
                method: 'login_user',
                args: [],
            }).then(function(result) {
                if(result === true){
                    self.field_name = ''
                    console.log()
                    var $label = $(ev.target);
                    self.label = $label;
                    self.field_name = $label[0].innerText;
                    if($label[0].localName === 'label'){
                        var value = $($label).replaceWith(`<input class="edit_label" data-label_for="${$(ev.target)[0].attributes.for.nodeValue}" value='${self.field_name}'>${$(self).text()}</input>`);
                    }
                }
            });
        },


        _onBlur: function(event) {
            var self = this;
            var ModelName = this.state.model
            var ViewType = this.state.viewType
            var inputModel = this.arch.attrs.string;
            var inputField = this.field_name
            var inputValue = $('.edit_label').val();
            var label_for = $(event.target).data('label_for');
            var field_tech_name;
            var inputFieldName;
            var ids = this.idsForLabels
            for (var item in ids){
                if(ids[item] === this.label[0].htmlFor){
                    var inputFieldName = item
                    var inputFieldLabel = this.field_name
                }
            }
//            try{
//                field_tech_name = $('#'+label_for)[0].attributes.name.nodeValue;
//                }
//            catch{
//                 var ids = this.idsForLabels
//                 for (var item in ids){
//                    if(ids[item] === this.label[0].htmlFor){
//                        var inputFieldName = item
//                        var inputFieldLabel = this.field_name
//                    }
//            }
//            }
            rpc.query({
                model: 'ir.ui.view',
                method: 'edit_xml_field_label',
                args: [ModelName, ViewType, inputField, inputFieldName, inputValue, field_tech_name, inputModel],
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


});