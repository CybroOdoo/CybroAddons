odoo.define('enhanced_survey_management.survey_submit', function (require){
'use strict';
    var SurveyFormWidget = require('survey.form');
    /*
        * Including custom events to SurveyFormWidget
    */
    SurveyFormWidget.include({
        events:{
                'change .o_file': '_onChangeFile',
                'change .o_survey_form_choice_item': '_onChangeChoiceItem',
                'click .o_survey_matrix_btn': '_onMatrixBtnClick',
                'click button[type="submit"]': '_onSubmit',
        },
        _prepareSubmitValues: function (formData, params) {
        var self = this;
        formData.forEach(function (value, key) {
            switch (key) {
                case 'csrf_token':
                case 'token':
                case 'page_id':
                case 'question_id':
                    params[key] = value;
                    break;
            }
        });
        // Get all question answers by question type
        var address = {}
        var names = {}
        var matrix = {}
        var self = this;
        this.$('[data-question-type]').each(function () {
            const questionType = $(this).data('questionType');
            const fieldName = this.name;
            const fieldValue = this.value;

            switch (questionType) {
                case 'text_box':
                case 'char_box':
                case 'numerical_box':
                case 'url':
                case 'email':
                case 'week':
                case 'color':
                case 'time':
                case 'range':
                case 'password':
                case 'month':
                case 'selection':
                    params[fieldName] = fieldValue;
                    break;

                case 'date':
                    params = self._prepareSubmitDates(params, fieldName, fieldValue, false);
                    break;

                case 'datetime':
                    params = self._prepareSubmitDates(params, fieldName, fieldValue, true);
                    break;

                case 'simple_choice_radio':
                case 'multiple_choice':
                    params = self._prepareSubmitChoices(params, $(this), $(this).data('name'));
                    break;

                case 'many2one':
                    params[fieldName] = [fieldValue, $(this).find("option:selected").data('value')];
                    break;

                case 'address':
                    address[fieldName] = fieldValue;
                    if (fieldName.endsWith('pin')) {
                        const baseName = fieldName.split("-")[0];
                        address[`${baseName}-country`] = self.$el.find(`#${baseName}-country`).val();
                        address[`${baseName}-state`] = self.$el.find(`#${baseName}-state`).val();
                        params[baseName] = address;
                        address = {};
                    }
                    break;

                case 'custom':
                    if (fieldName === 'matrix-end') {
                        params[this.id] = matrix;
                    } else if ($(this).attr('id') === 'select' && fieldName) {
                        matrix[fieldName] = $(this).find("option:selected").data('value');
                    } else if ($(this).attr('id') !== 'select' && fieldName) {
                        matrix[fieldName] = fieldValue;
                    }
                    break;

                case 'matrix':
                    params = self._prepareSubmitAnswersMatrix(params, $(this));
                    break;

                case 'name':
                    names[fieldName] = fieldValue;
                    if (fieldName.endsWith('last')) {
                        params[fieldName.split("-")[0]] = names;
                        names = {}; // Clear after use
                    }
                    break;

                case 'file':
                    const file = $(this)[0].files[0];
                    if (file) {
                        params[fieldName] = [$(this).data('file-name'), file.name];
                    }
                    break;

                case 'many2many':
                    params[fieldName] = self.$el.find(`.${fieldName}`).val();
                    break;
                }
            });
        }
        _onChangeFile: function (ev) {
            /*
                *  method to save attachments
            */
            const element = this.$(ev.target);
            for (var i=0; i < element.length; i++){
                const elements = $(element[i])
                if (element[i].files[0] && elements.data('file') === parseInt(elements.attr('name'))) {
                    var file_name = element[i].files[0]['name']
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        elements.attr('data-file-name', reader.result.split(',')[1])
                        elements.attr('data-file', file_name)
                    };
                    reader.readAsDataURL(element[i].files[0]);
                }
            }
        },
    })
})
