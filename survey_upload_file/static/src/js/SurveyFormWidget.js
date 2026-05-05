/** @odoo-module */
import { patch } from "@web/core/utils/patch";

const SurveyForm = odoo.loader.modules.get("@survey/interactions/survey_form").SurveyForm;

patch(SurveyForm.prototype, {
    prepareSubmitValues(formData, params) {
        super.prepareSubmitValues(...arguments);
        for (const el of this.el.querySelectorAll("[data-question-type='upload_file']")) {
            const data = el.dataset.oeData || "[]";
            const fileNames = el.dataset.oeFileName || "[]";
            params[el.name] = [data, fileNames];
        }
    },
});
