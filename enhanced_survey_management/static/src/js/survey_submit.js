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
                'click input[type="radio"]': '_onRadioChoiceClick',
                'click button[type="submit"]': '_onSubmit',
                'click .o_survey_choice_img img': '_onChoiceImgClick',
                'focusin .form-control': '_updateEnterButtonText',
                'focusout .form-control': '_updateEnterButtonText'
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
            switch ($(this).data('questionType')) {
                case 'text_box':
                case 'char_box':
                case 'numerical_box':
                    params[this.name] = this.value;
                    break;
                case 'date':
                    params = self._prepareSubmitDates(params, this.name, this.value, false);
                    break;
                case 'datetime':
                    params = self._prepareSubmitDates(params, this.name, this.value, true);
                    break;
                case 'simple_choice_radio':
                case 'multiple_choice':
                    params = self._prepareSubmitChoices(params, $(this), $(this).data('name'));
                    break;
                case 'url':
                    params[this.name] = this.value;
                    break;
                case 'email':
                    params[this.name] = this.value;
                    break;
                case 'many2one':
                    params[this.name] = [this.value, $(this).find("option:selected").attr('data-value')];
                    break;
                case 'week':
                    params[this.name] = this.value;
                    break;
                case 'color':
                    params[this.name] = this.value;
                    break;
                case 'time':
                    params[this.name] = this.value;
                    break;
                case 'range':
                    params[this.name] = this.value;
                    break;
                case 'password':
                    params[this.name] = this.value;
                    break;
                case 'month':
                    params[this.name] = this.value
                    break;
                case 'address':
                    address[this.name] = this.value
                    if (this.name.endsWith('pin')){
                        address[this.name.split("-")[0]+'-country'] = self.$el.find(`#${this.name.split("-")[0]+'-country'}`).val(),
                        address[this.name.split("-")[0]+'-state'] = self.$el.find(`#${this.name.split("-")[0]+'-state'}`).val()
                        params[this.name.split("-")[0]] = address
                        address = {}
                        break;
                    }
                    break;
                case 'custom':
                    if (this.name == 'matrix-end'){
                        params[this.id] = matrix}
                    if ($(this).attr('id') === 'select' && this.name){
                       matrix[this.name] = $(this).find("option:selected").attr('data-value')}
                    if ($(this).attr('id') !== 'select' && this.name){
                       matrix[this.name] = this.value
                    }
                case 'matrix':
                    params = self._prepareSubmitAnswersMatrix(params, $(this));
                    break;
                case 'name':
                    names[this.name] = this.value
                    if (this.name.endsWith('last')){
                        params[this.name.split("-")[0]] = names
                        break;
                    }
                    break;
                case 'selection':
                    params[this.name] = this.value
                    break;
                case 'file':
                    if ($(this)[0].files[0]){
                        params[this.name] = [$(this).data('file-name'), $(this)[0].files[0]['name']]
                        break;
                    }
                    break;
                case 'many2many':
                    params[this.name] = self.$el.find(`.${this.name}`).val()
                    break;
                    }
                });
             },
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
