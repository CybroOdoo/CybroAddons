odoo.define('survey_upload_file', function (require) {
    'use strict';

    var SurveyFormWidget = require('survey.form');
    var core = require('web.core');

    SurveyFormWidget.include({
        events: _.extend({}, SurveyFormWidget.prototype.events, {
            'change .o_survey_upload_file': '_onFileChange',
        }),
        // On adding file function
        _onFileChange: function (event) {
            var self = this;
            var files = event.target.files;
            var fileNames = [];
            var dataURLs = [];

            // Loop through the selected files
            for (let i = 0; i < files.length; i++) {
                var reader = new FileReader();
                reader.readAsDataURL(files[i]);

                reader.onload = function (e) {
                    var file = files[i];
                    var filename = file.name;
                    var dataURL = e.target.result.split(',')[1]; // split base64 data

                    fileNames.push(filename);
                    dataURLs.push(dataURL);

                    // Set the attributes for the input element
                    var $input = $(event.target);
                    $input.attr('data-oe-data', JSON.stringify(dataURLs));
                    $input.attr('data-oe-file_name', JSON.stringify(fileNames));

                    // Find the corresponding fileList div based on the question ID (matching data attribute)
                    var $fileListContainer = $(event.target)
                        .closest('.o_survey_upload_container')
                        .find('#fileList');

                    var questionId = $fileListContainer.attr('data');

                    // Check if the fileList div corresponds to the input clicked (based on question ID)
                    if ($fileListContainer.attr('data') == event.target.name) {
                        // Clear previous contents of the file list
                        $fileListContainer.html('');

                        // Create a new list of files
                        var ul = document.createElement('ul');
                        fileNames.forEach(function (fileName) {
                            var li = document.createElement('li');
                            li.textContent = fileName;
                            ul.appendChild(li);
                        });

                        // Create a delete button
                        var deleteBtn = document.createElement('button');
                        deleteBtn.textContent = 'Delete All';
                        deleteBtn.addEventListener('click', function () {
                            // Clear file list and reset input attributes
                            $fileListContainer.html('');
                            $input.attr('data-oe-data', '');
                            $input.attr('data-oe-file_name', '');
                            $input.val(''); // Clear the file input
                        });

                        // Append the file list and delete button to the fileList div
                        $fileListContainer.append(ul);
                        $fileListContainer.append(deleteBtn);
                    }
                };
            }
        },
        // Get all question answers by question type
        _prepareSubmitValues: function (formData, params) {
            this._super(formData, params);
            this.$('[data-question-type]').each(function () {
                if ($(this).data('questionType') === 'upload_file') {
                    params[this.name] = [
                        $(this).data('oe-data'),
                        $(this).data('oe-file_name'),
                    ];
                }
            });
        },
        // Add file upload required case
        _validateForm: function ($form, formData) {
            this._super($form, formData);
            var errors = {};
            $form.find('[data-question-type]').each(function () {
                var $input = $(this);
                var $questionWrapper = $input.closest('.js_question-wrapper');
                var questionRequired = $questionWrapper.data('required');
                var constrErrorMsg = $questionWrapper.data('constrErrorMsg');
                var validationErrorMsg = $questionWrapper.data('validationErrorMsg');
                var questionId = $questionWrapper.attr('id');

                switch ($input.data('questionType')) {
                    case 'upload_file':
                        if (questionRequired && !$input.val()) {
                            errors[questionId] = constrErrorMsg;
                        }
                        break;
                }
            });

            if (_.keys(errors).length > 0) {
                this._showErrors(errors);
                return false;
            }

            return true;
        },
    });
});
                                