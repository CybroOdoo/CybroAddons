/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class VendorQuestionnaire extends Interaction {
    static selector = "[data-vq-form]";

    setup() {
        this.answeredQuestions = 0;
        this.totalQuestions = 0;
        this.percentage = 0;
        this.isSubmitting = false;
    }

    start() {
        this.buildAccordion();
        this.updateProgress();
    }

    dynamicContent = {
        _root: {
            "t-on-input": (ev) => this.onFormInput(ev),
            "t-on-change": (ev) => this.onFormInput(ev),
            "t-on-submit": (ev) => this.onSubmit(ev),
        },
        "[data-vq-progress-bar]": {
            "t-att-style": () => ({ width: `${this.percentage}%` }),
        },
        ".progress[role='progressbar']": {
            "t-att-aria-valuenow": () => String(this.percentage),
        },
        "[data-vq-progress-text]": {
            "t-out": () => `${this.answeredQuestions} / ${this.totalQuestions} questions answered`,
        },
        "[data-vq-progress-percentage]": {
            "t-out": () => `${this.percentage}%`,
        },
        "[data-vq-submit-button]": {
            "t-att-disabled": () => this.isSubmitting || false,
        },
        "[data-vq-submit-label]": {
            "t-att-class": () => ({ "d-none": this.isSubmitting }),
        },
        "[data-vq-submitting-label]": {
            "t-att-class": () => ({ "d-none": !this.isSubmitting }),
        },
    };

    buildAccordion() {
        const accordion = this.el.querySelector("[data-vq-accordion]");
        const questionSource = this.el.querySelector("[data-vq-question-source]");

        if (!accordion || !questionSource) {
            return;
        }

        const sectionGroups = [];
        const sectionsByName = new Map();
        questionSource.querySelectorAll("[data-vq-section]").forEach((question) => {
            const sectionName = question.dataset.vqSection || "Questions";
            if (!sectionsByName.has(sectionName)) {
                const group = { name: sectionName, questions: [] };
                sectionsByName.set(sectionName, group);
                sectionGroups.push(group);
            }
            sectionsByName.get(sectionName).questions.push(question);
        });

        const accordionFragment = document.createDocumentFragment();
        sectionGroups.forEach((section, index) => {
            const item = document.createElement("section");
            const headingId = `vqSectionHeading${index}`;
            const collapseId = `vqSectionCollapse${index}`;
            const isFirstSection = index === 0;

            item.className = "accordion-item";
            const heading = document.createElement("h2");
            heading.className = "accordion-header";
            heading.id = headingId;

            const button = document.createElement("button");
            button.className = `accordion-button${isFirstSection ? "" : " collapsed"}`;
            button.type = "button";
            button.dataset.bsToggle = "collapse";
            button.dataset.bsTarget = `#${collapseId}`;
            button.setAttribute("aria-expanded", String(isFirstSection));
            button.setAttribute("aria-controls", collapseId);

            const title = document.createElement("span");
            title.className = "vq-accordion-title";
            title.textContent = section.name;
            const meta = document.createElement("span");
            meta.className = "vq-accordion-meta";
            meta.textContent = `${section.questions.length} ${section.questions.length === 1 ? "question" : "questions"}`;
            title.appendChild(meta);
            button.appendChild(title);
            heading.appendChild(button);

            const collapse = document.createElement("div");
            collapse.id = collapseId;
            collapse.className = `accordion-collapse collapse${isFirstSection ? " show" : ""}`;
            collapse.setAttribute("aria-labelledby", headingId);

            const body = document.createElement("div");
            body.className = "accordion-body";
            section.questions.forEach((question) => body.appendChild(question));
            collapse.appendChild(body);
            item.append(heading, collapse);
            accordionFragment.appendChild(item);
        });

        accordion.appendChild(accordionFragment);
        questionSource.remove();
    }

    onFormInput(ev) {
        this.updateProgress();
    }

    updateProgress() {
        const questions = Array.from(this.el.querySelectorAll(".vq-question-card"));
        this.answeredQuestions = questions.filter((question) =>
            Array.from(question.querySelectorAll("input, textarea, select")).some((control) => {
                if (control.disabled) {
                    return false;
                }
                if (control.type === "radio" || control.type === "checkbox") {
                    return control.checked;
                }
                if (control.type === "file") {
                    return control.files.length > 0;
                }
                return Boolean(control.value.trim());
            })
        ).length;
        this.totalQuestions = questions.length;
        this.percentage = this.totalQuestions
            ? Math.round((this.answeredQuestions / this.totalQuestions) * 100)
            : 0;
    }

    onSubmit(ev) {
        this.isSubmitting = true;
    }
}

registry.category("public.interactions").add("pharma_vendor_qualification.vendor_questionnaire", VendorQuestionnaire);


