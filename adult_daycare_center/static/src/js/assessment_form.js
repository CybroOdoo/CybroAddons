/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

const ADULT_AGE = 18;
const UNDERAGE_MESSAGE = "You must be 18 years of age or older to submit this form.";

export class AssessmentRequestForm extends Interaction {
    static selector = "#assessment_contactus_form";

    dynamicContent = {
        "#living_arrangement": { "t-on-change": this.onLivingArrangementChange },
        "input[name='experience']": { "t-on-change": this.onExperienceChange },
        "input[name='diet']": { "t-on-change": this.onDietChange },
        "#birth_date": { "t-on-change": this.onBirthDateChange },
        _root: { "t-on-submit": this.onFormSubmit },
    };

    start() {
        // Initial checks on page load.
        this.onLivingArrangementChange();
        this.onExperienceChange();
        this.onDietChange();
        this.setBirthDateMax();
    }

    /**
     * Restrict the date picker so that no date less than 18 years ago can be
     * selected.
     */
    setBirthDateMax() {
        const birthDateInput = this.el.querySelector("#birth_date");
        if (!birthDateInput) {
            return;
        }
        const today = new Date();
        const maxDate = new Date(
            today.getFullYear() - ADULT_AGE, today.getMonth(), today.getDate()
        );
        // Build the value from local date parts to avoid UTC shifts.
        const month = String(maxDate.getMonth() + 1).padStart(2, "0");
        const day = String(maxDate.getDate()).padStart(2, "0");
        birthDateInput.setAttribute("max", `${maxDate.getFullYear()}-${month}-${day}`);
    }

    /**
     * @param {string} value birth date as YYYY-MM-DD
     * @returns {boolean} true if the applicant is 18 or older
     */
    isAdult(value) {
        if (!value) {
            return false;
        }
        const birthDate = new Date(value);
        if (isNaN(birthDate.getTime())) {
            return false;
        }
        const today = new Date();
        let age = today.getFullYear() - birthDate.getFullYear();
        const monthDiff = today.getMonth() - birthDate.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
            age--;
        }
        return age >= ADULT_AGE;
    }

    /**
     * Show a field wrapper and make its input required, or hide it and drop
     * the required flag.
     *
     * @param {HTMLElement} inputEl
     * @param {boolean} visible
     */
    toggleField(inputEl, visible) {
        const fieldEl = inputEl.closest(".s_website_form_field");
        if (fieldEl) {
            fieldEl.style.display = visible ? "block" : "none";
        }
        inputEl.required = visible;
    }

    onBirthDateChange() {
        const birthDateInput = this.el.querySelector("#birth_date");
        if (!birthDateInput) {
            return;
        }
        if (birthDateInput.value && !this.isAdult(birthDateInput.value)) {
            birthDateInput.setCustomValidity(UNDERAGE_MESSAGE);
        } else {
            birthDateInput.setCustomValidity("");
        }
        birthDateInput.reportValidity();
    }

    /**
     * Final safety check on submit, in case the field was never changed.
     *
     * @param {Event} ev
     */
    onFormSubmit(ev) {
        const birthDateInput = this.el.querySelector("#birth_date");
        if (!birthDateInput) {
            return;
        }
        if (!this.isAdult(birthDateInput.value)) {
            birthDateInput.setCustomValidity(UNDERAGE_MESSAGE);
            birthDateInput.reportValidity();
            ev.preventDefault();
            ev.stopPropagation();
        } else {
            birthDateInput.setCustomValidity("");
        }
    }

    onLivingArrangementChange() {
        const livingArrangement = this.el.querySelector("#living_arrangement");
        const livingWithWhomInput = this.el.querySelector("#living_with_whom");
        const relationWithLivingInput = this.el.querySelector("#relation_with_living");
        if (!livingArrangement || !livingWithWhomInput || !relationWithLivingInput) {
            return;
        }
        const livesAlone = ["home_alone", "alone_single"].includes(livingArrangement.value);
        this.toggleField(livingWithWhomInput, !livesAlone);
        this.toggleField(relationWithLivingInput, !livesAlone);
    }

    onExperienceChange() {
        const experienceYes = this.el.querySelector("#yes");
        const whereWhenInput = this.el.querySelector("#where_when");
        if (!experienceYes || !whereWhenInput) {
            return;
        }
        this.toggleField(whereWhenInput, experienceYes.checked);
    }

    onDietChange() {
        const dietYes = this.el.querySelector("#dietYes");
        const dietDetailInput = this.el.querySelector("#diet_detail");
        if (!dietYes || !dietDetailInput) {
            return;
        }
        this.toggleField(dietDetailInput, dietYes.checked);
    }
}

registry
    .category("public.interactions")
    .add("adult_daycare_center.assessment_request_form", AssessmentRequestForm);
