/** @odoo-module */
import { patch } from "@web/core/utils/patch";

const SurveyForm = odoo.loader.modules.get("@survey/interactions/survey_form").SurveyForm;

async function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result || "";
            resolve(String(result).split(",")[1] || "");
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
    });
}

function renderFileList(containerEl, fileNames, clearCallback) {
    containerEl.replaceChildren();
    if (!fileNames.length) {
        return;
    }
    const ul = document.createElement("ul");
    for (const fileName of fileNames) {
        const li = document.createElement("li");
        li.textContent = fileName;
        ul.appendChild(li);
    }
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.textContent = "Delete All";
    deleteBtn.addEventListener("click", clearCallback);
    containerEl.appendChild(ul);
    containerEl.appendChild(deleteBtn);
}

patch(SurveyForm.prototype, {
    setup() {
        super.setup(...arguments);
        this._uploadFileChangeHandler = this._uploadFileChangeHandler.bind(this);
    },

    start() {
        super.start(...arguments);
        this.el.addEventListener("change", this._uploadFileChangeHandler);
    },

    _uploadFileChangeHandler(event) {
        const inputEl = event.target;
        if (!(inputEl instanceof HTMLInputElement)) {
            return;
        }
        if (inputEl.type !== "file" || !inputEl.classList.contains("o_survey_upload_file")) {
            return;
        }
        this._handleUploadFileChange(inputEl);
    },

    async _handleUploadFileChange(inputEl) {
        const files = Array.from(inputEl.files || []);
        const isMultiple = inputEl.hasAttribute("multiple");

        let fileNames = [];
        let dataURLs = [];

        if (isMultiple) {
            try {
                fileNames = JSON.parse(inputEl.dataset.oeFileName || "[]");
                dataURLs = JSON.parse(inputEl.dataset.oeData || "[]");
            } catch (e) {
                console.warn("Could not parse existing data:", e);
            }
        }

        for (const file of files) {
            try {
                const dataURL = await readFileAsBase64(file);
                dataURLs.push(dataURL);
                fileNames.push(file.name);
            } catch (error) {
                console.warn(`Could not read file ${file.name}:`, error);
            }
        }
        inputEl.dataset.oeData = JSON.stringify(dataURLs);
        inputEl.dataset.oeFileName = JSON.stringify(fileNames);

        const questionWrapper = inputEl.closest(".js_question-wrapper");
        const listEl = questionWrapper?.querySelector(
            `.o_survey_upload_list[data-question-id='${inputEl.name}']`
        );
        if (!listEl) {
            return;
        }

        renderFileList(listEl, fileNames, () => {
            inputEl.value = "";
            inputEl.dataset.oeData = "";
            inputEl.dataset.oeFileName = "";
            renderFileList(listEl, [], () => {});
        });

        // Update the input files so that the browser native UI shows the correct file count
        try {
            const dt = new DataTransfer();
            if (fileNames.length > 0) {
                const countText = fileNames.length === 1 ? "1 file" : `${fileNames.length} files`;
                dt.items.add(new File([""], countText));
            }
            inputEl.files = dt.files;
        } catch (e) {
            // Fallback for older browsers
            inputEl.value = "";
        }
    },
});