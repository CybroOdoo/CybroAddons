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
            this.rpc = this.bindService("rpc");
        },
       _onFileChange: function (ev) {
            const inputEl = ev.currentTarget;
            const files = ev.target.files;
            if (!files || files.length === 0) return;

            const readFile = (file) => {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => {
                        const base64 = reader.result.split(',')[1];
                        resolve({
                            data: base64,
                            name: file.name
                        });
                    };
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });
            };

            Promise.all([...files].map(readFile)).then(results => {
                inputEl.setAttribute('data-oe-data', JSON.stringify(results));
            });
        }

    });
export default publicWidget.registry.SurveyFormUpload;
