/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import SurveyFormWidget from '@survey/js/survey_form';
import SurveyPreloadImageMixin from "@survey/js/survey_preload_image_mixin";
/**  Extends publicWidget to create "SurveyFormUpload" */
publicWidget.registry.SurveyFormUpload = publicWidget.Widget.extend(SurveyPreloadImageMixin, {
        selector: '.o_survey_form',
        events: {
            'change .o_survey_upload_file': '_onFileChange',
        },
        init() {
            this._super(...arguments);
        },
        /** On adding file function */
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
                    var dataURL = e.target.result.split(',')[1]; /**  split base64 data */
                    fileNames.push(filename);
                    dataURLs.push(dataURL);
                    /**  Set the data-oe-data and data-oe-file_name attributes of the input element self call el */
                    var $input = self.$el.find('input.o_survey_upload_file');

                    $input.attr('data-oe-data') && dataURLs.concat(JSON.parse($input.attr('data-oe-data')))
                    $input.attr('data-oe-data', JSON.stringify(dataURLs));
                    $input.attr('data-oe-file_name') && fileNames.concat(JSON.parse($input.attr('data-oe-file_name')))
                    $input.attr('data-oe-file_name', JSON.stringify(fileNames));
                    // Create file list elements
                    var fileList = document.getElementById('fileList');
                    var existingUl = fileList.querySelector('ul')
                    if(existingUl){

                        fileNames.forEach(function(fileName) {
                            const exists = Array.from(existingUl.children).some(
                                (li) => li.textContent === fileName
                            );
                            if(!exists){
                                var li = document.createElement('li');
                                li  .textContent = fileName;
                                existingUl.appendChild(li);
                            }
                        });
                    }
                    else{
                        var ul = document.createElement('ul');
                        fileNames.forEach(function(fileName) {
                            var li = document.createElement('li');
                            li.textContent = fileName;
                            ul.appendChild(li);
                        });
                        fileList.appendChild(ul);
                    }

                    // Create delete button
                    var deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'Delete All';
                    deleteBtn.id = "delete_button"
                    deleteBtn.addEventListener('click', function() {
                        // Clear file list
                        fileList.innerHTML = '';
                        // Clear input field attributes
                        $input.attr('data-oe-data', '');
                        $input.attr('data-oe-file_name', '');
                        self.$el.find('input[type="file"]').val('');
                    });
                    // Append file list and delete button to file input container
                    var existingBtn = fileList.querySelector('#delete_button');
                    if(existingBtn){
                        existingBtn.remove();
                    }
                    fileList.appendChild(deleteBtn);

                }
            }
        },
    });
export default publicWidget.registry.SurveyFormUpload;
