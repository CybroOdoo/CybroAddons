/** @odoo-module */
import SurveyFormWidget from '@survey/js/survey_form';
SurveyFormWidget.include({
    /** Get all question answers by question type */
    _prepareSubmitValues(formData, params) {
        this._super(...arguments);
        this.$('[data-question-type]').each(function () {
        if ($(this).data('questionType') === 'upload_file'){
             params[this.name] = [$(this).data('oe-data'), $(this).data('oe-file_name')];
        }
        });
    },
});
