odoo.define('survey_upload_file', function (require) {
    'use strict';

    var SurveyFormWidget = require('survey.form');
    var core = require('web.core');

    SurveyFormWidget.include({
        events: _.extend({}, SurveyFormWidget.prototype.events,{
        'change .o_survey_upload_file': '_onFileChange',
        }),

        start: function () {
            return this._super.apply(this, arguments)
        },
        //On adding file function
        _onFileChange: function(event) {
            var self = this;
            var files = event.target.files;
            var fileNames = [];
            var dataURLs = [];
            for (let i = 0; i < files.length; i++) {
                var reader = new FileReader();
                reader.readAsDataURL(files[i]);

                reader.onload = function(e) {
                    var file = files[i];
                    var filename = file.name;
                    var dataURL = e.target.result.split(',')[1]; // split base64 data
                    fileNames.push(filename);
                    dataURLs.push(dataURL);

                    // set the data-oe-data and data-oe-file_name attributes of the input element
//                    self call el
                    var $input = self.$el.find('input.o_survey_upload_file');
                    $input.attr('data-oe-data', JSON.stringify(dataURLs));
                    $input.attr('data-oe-file_name', JSON.stringify(fileNames));

                    // create file list elements
                    var fileList = document.getElementById('fileList');
                    fileList.innerHTML = ''; // clear previous contents of file list

                    var ul = document.createElement('ul');
                    fileNames.forEach(function(fileName) {
                      var li = document.createElement('li');
                      li.textContent = fileName;
                      ul.appendChild(li);
                    });

                    // create delete button
                    var deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Delete All';
                    deleteBtn.addEventListener('click', function() {
                        // clear file list
                        fileList.innerHTML = '';
                        // clear input field attributes
                        $input.attr('data-oe-data', '');
                        $input.attr('data-oe-file_name', '');
                        self.$el.find('input[type="file"]').val('');
                    });

                    // append file list and delete button to file input container
                    fileList.appendChild(ul);
                    fileList.appendChild(deleteBtn);
                }
            }
        },
        // Get all question answers by question type
        _prepareSubmitValues: function (formData, params) {
            this._super(formData, params)
            this.$('[data-question-type]').each(function () {
            if ($(this).data('questionType') === 'upload_file'){
                 params[this.name] = [$(this).data('oe-data'), $(this).data('oe-file_name')];
            }
            });
        },
    });
    });
