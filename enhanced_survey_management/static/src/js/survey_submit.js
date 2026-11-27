/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { SurveyForm } from "@survey/interactions/survey_form";

patch(SurveyForm.prototype, {
    start() {
        super.start();
        this.addListener(this.el, "change", (ev) => {
            if (ev.target.matches(".o_file")) {
                this._onChangeFile(ev);
            }
        });
    },

    validateForm(formEl, formData) {
        const baseValid = super.validateForm(formEl, formData);
        const errors = {};
        const validationUrlMsg = _t("This answer must be a valid URL.");
        const validationEmailMsg = _t("This answer must be an email address.");

        const inactiveQuestionIds = this.options.sessionInProgress
            ? []
            : this.getInactiveConditionalQuestionIds();

        for (const inputEl of formEl.querySelectorAll("[data-question-type]")) {
            const questionWrapperEl = inputEl.closest(".o_survey_question");
            if (!questionWrapperEl) {
                continue;
            }
            const questionId = questionWrapperEl.id;
            if (inactiveQuestionIds.includes(parseInt(questionId))) {
                continue;
            }
            const questionRequired = questionWrapperEl.hasAttribute("data-required");
            const constrErrorMsg =
                questionWrapperEl.dataset.constrErrorMsg ||
                _t("This question requires an answer.");
            const qType = inputEl.dataset.questionType;

            if (qType === "url") {
                if (questionRequired && !inputEl.value) {
                    errors[questionId] = constrErrorMsg;
                } else if (inputEl.value && !this.validateUrl(inputEl.value)) {
                    errors[questionId] = validationUrlMsg;
                }
            } else if (qType === "email") {
                if (questionRequired && !inputEl.value) {
                    errors[questionId] = constrErrorMsg;
                } else if (inputEl.value && !this.validateEmail(inputEl.value)) {
                    errors[questionId] = validationEmailMsg;
                }
            }
        }

        if (Object.keys(errors).length > 0) {
            this.showErrors(errors);
            return false;
        }

        return baseValid;
    },

    validateUrl(url) {
        if (!url || typeof url !== "string" || !url.trim() || url.includes(" ")) {
            return false;
        }
        try {
            const testUrl = url.includes("://") ? url : `https://${url}`;
            const parsed = new URL(testUrl);
            if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) {
                return false;
            }
            if (parsed.hostname === "localhost") {
                return true;
            }
            const parts = parsed.hostname.split(".");
            return parts.length >= 2 && parts[parts.length - 1].length >= 2;
        } catch {
            return false;
        }
    },

    prepareSubmitValues(formData, params) {
        super.prepareSubmitValues(formData, params);

        let address = {};
        let names = {};
        const matrix = {};

        const customInputs = this.el.querySelectorAll("[data-question-type]");

        customInputs.forEach((input) => {
            const qType = input.dataset.questionType;

            switch (qType) {
                case "url":
                case "email":
                case "week":
                case "color":
                case "time":
                case "range":
                case "password":
                case "month":
                case "selection":
                case "qr":
                case "barcode":
                    params[input.name] = input.value;
                    break;

                case "many2one": {
                    const option =
                        input.selectedOptions?.[0] ||
                        input.querySelector(`option[value="${CSS.escape(input.value)}"]`);
                    if (option) {
                        params[input.name] = [
                            input.value,
                            option.dataset.value || "",
                        ];
                    }
                    break;
                }

                case "address":
                    address[input.name] = input.value;
                    if (input.name.endsWith("pin")) {
                        const base = input.name.split("-")[0];
                        const countryEl = this.el.querySelector(`#${CSS.escape(`${base}-country`)}`);
                        const stateEl = this.el.querySelector(`#${CSS.escape(`${base}-state`)}`);
                        address[`${base}-country`] = countryEl?.value || "";
                        address[`${base}-state`] = stateEl?.value || "";
                        params[base] = address;
                        address = {};
                    }
                    break;

                case "custom":
                    if (input.name === "matrix-end") {
                        params[input.id] = matrix;
                    } else if (input.name) {
                        matrix[input.name] =
                            input.tagName === "SELECT"
                                ? input.selectedOptions?.[0]?.dataset.value || ""
                                : input.value;
                    }
                    break;

                case "name":
                    names[input.name] = input.value;
                    if (input.name.endsWith("last")) {
                        params[input.name.split("-")[0]] = names;
                        names = {};
                    }
                    break;

                case "file":
                    if (input.files?.[0]) {
                        params[input.name] = [
                            input.dataset.fileName,
                            input.files[0].name,
                        ];
                    }
                    break;

                case "many2many": {
                    if (input.selectedOptions) {
                        params[input.name] = Array.from(input.selectedOptions)
                            .map((opt) => opt.value)
                            .filter(Boolean)
                            .join(", ");
                    } else {
                        const el = this.el.querySelector(`.${CSS.escape(input.name)}`);
                        if (el) {
                            params[input.name] = el.value;
                        }
                    }
                    break;
                }
            }
        });
    },

    _onChangeFile(ev) {
        const input = ev.target;

        if (!input.files?.[0]) {
            return;
        }

        const reader = new FileReader();
        reader.onloadend = () => {
            input.dataset.fileName = reader.result.split(",")[1];
            input.dataset.file = input.files[0].name;
        };
        reader.readAsDataURL(input.files[0]);
    },
});
