/** @odoo-module */
import { patch } from "@web/core/utils/patch";

const SurveyForm = odoo.loader.modules.get("@survey/interactions/survey_form").SurveyForm;

async function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result || "";
            const data = String(result).split(",")[1] || "";
            console.debug("[survey_upload_file] file read", {
                name: file.name,
                fileSize: file.size,
                base64Length: data.length,
            });
            resolve(data);
        };
        reader.onerror = () => {
            console.error("[survey_upload_file] file read failed", file.name, reader.error);
            reject(reader.error);
        };
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
        this._uploadFileClickHandler = this._uploadFileClickHandler.bind(this);
    },

    start() {
        super.start(...arguments);
        this.el.addEventListener("change", this._uploadFileChangeHandler);
        this.el.addEventListener("click", this._uploadFileClickHandler);
        for (const container of this.el.querySelectorAll(".o_survey_upload_container")) {
            this._updateListVisibility(container);
        }
    },

    onNextScreenDone() {
        super.onNextScreenDone(...arguments);
        for (const container of this.el.querySelectorAll(".o_survey_upload_container")) {
            this._updateListVisibility(container);
        }
    },

    _uploadFileClickHandler(event) {
        const removeExistingBtn = event.target.closest(".o_survey_remove_existing_btn");
        if (removeExistingBtn) {
            const container = removeExistingBtn.closest(".o_survey_upload_container");
            const inputEl = container?.querySelector("input.o_survey_upload_file");
            const existingId = removeExistingBtn.dataset.existingId;
            if (inputEl && existingId) {
                const existingIds = (inputEl.dataset.existingIds || "")
                    .split(",")
                    .filter((id) => id && id !== existingId);
                inputEl.dataset.existingIds = existingIds.join(",");
                removeExistingBtn.closest(".o_survey_file_item")?.remove();
                this._updateListVisibility(container);
            }
            return;
        }

        const removeNewBtn = event.target.closest(".o_survey_remove_new_btn");
        if (removeNewBtn) {
            const container = removeNewBtn.closest(".o_survey_upload_container");
            const inputEl = container?.querySelector("input.o_survey_upload_file");
            const index = parseInt(removeNewBtn.dataset.newIndex, 10);
            if (inputEl && !isNaN(index)) {
                let dataURLs = [];
                let fileNames = [];
                try {
                    dataURLs = JSON.parse(inputEl.dataset.oeData || "[]");
                    fileNames = JSON.parse(inputEl.dataset.oeFileName || "[]");
                } catch (_) {}
                dataURLs.splice(index, 1);
                fileNames.splice(index, 1);
                inputEl.dataset.oeData = JSON.stringify(dataURLs);
                inputEl.dataset.oeFileName = JSON.stringify(fileNames);
                this._renderUploadList(inputEl);
            }
            return;
        }

        const deleteAllBtn = event.target.closest(".o_survey_delete_all_btn");
        if (deleteAllBtn) {
            const container = deleteAllBtn.closest(".o_survey_upload_container");
            const inputEl = container?.querySelector("input.o_survey_upload_file");
            if (inputEl) {
                inputEl.value = "";
                inputEl.dataset.oeData = "[]";
                inputEl.dataset.oeFileName = "[]";
                inputEl.dataset.existingIds = "";
                const listEl = container.querySelector(".o_survey_upload_list");
                if (listEl) {
                    listEl.replaceChildren();
                }
                this._updateListVisibility(container);
            }
        }
    },

    _uploadFileChangeHandler(event) {
        const inputEl = event.target;
        if (!(inputEl instanceof HTMLInputElement)) {
            return;
        }
        if (inputEl.type !== "file" || !inputEl.classList.contains("o_survey_upload_file")) {
            return;
        }
        this._uploadFileReadPromises ??= new Set();
        const readPromise = this._handleUploadFileChange(inputEl);
        this._uploadFileReadPromises.add(readPromise);
        readPromise.then(
            () => this._uploadFileReadPromises.delete(readPromise),
            () => this._uploadFileReadPromises.delete(readPromise)
        );
    },

    async _handleUploadFileChange(inputEl) {
        const files = Array.from(inputEl.files || []);
        if (!files.length) {
            return;
        }

        const isMultiple = Boolean(inputEl.multiple);
        let dataURLs = [];
        let fileNames = [];

        if (isMultiple) {
            try {
                dataURLs = JSON.parse(inputEl.dataset.oeData || "[]");
                fileNames = JSON.parse(inputEl.dataset.oeFileName || "[]");
            } catch (_) {
                dataURLs = [];
                fileNames = [];
            }
        } else {
            // Single file upload replaces any previous or existing file
            inputEl.dataset.existingIds = "";
            const container = inputEl.closest(".o_survey_upload_container");
            container?.querySelectorAll(".o_survey_existing_item").forEach((el) => el.remove());
        }

        for (const file of files) {
            dataURLs.push(await readFileAsBase64(file));
            fileNames.push(file.name);
        }

        inputEl.dataset.oeData = JSON.stringify(dataURLs);
        inputEl.dataset.oeFileName = JSON.stringify(fileNames);
        inputEl.value = "";

        this._renderUploadList(inputEl);
    },

    _renderUploadList(inputEl) {
        const container = inputEl.closest(".o_survey_upload_container");
        if (!container) {
            return;
        }
        const listEl = container.querySelector(".o_survey_upload_list");
        if (!listEl) {
            return;
        }

        let newFileNames = [];
        try {
            newFileNames = JSON.parse(inputEl.dataset.oeFileName || "[]");
        } catch (_) {}

        let newFilesUl = listEl.querySelector(".o_survey_new_files");
        if (!newFilesUl) {
            newFilesUl = document.createElement("ul");
            newFilesUl.className = "o_survey_new_files list-unstyled mb-2";
            listEl.appendChild(newFilesUl);
        }
        newFilesUl.replaceChildren();

        for (let i = 0; i < newFileNames.length; i++) {
            const name = newFileNames[i];
            const li = document.createElement("li");
            li.className =
                "o_survey_file_item o_survey_new_item d-flex align-items-center justify-content-between p-2 mb-1 border rounded bg-white";

            const span = document.createElement("span");
            span.className = "text-truncate me-2";

            const fileIcon = document.createElement("i");
            fileIcon.className = "fa fa-file text-success me-2";
            span.appendChild(fileIcon);

            const nameSpan = document.createElement("span");
            nameSpan.textContent = name;
            span.appendChild(nameSpan);

            const badge = document.createElement("span");
            badge.className = "badge bg-success-subtle text-success ms-1";
            badge.textContent = "New";
            span.appendChild(badge);

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "btn btn-sm btn-outline-danger o_survey_remove_new_btn";
            btn.dataset.newIndex = String(i);
            btn.title = "Remove file";

            const trashIcon = document.createElement("i");
            trashIcon.className = "fa fa-trash";
            btn.appendChild(trashIcon);

            li.appendChild(span);
            li.appendChild(btn);
            newFilesUl.appendChild(li);
        }

        this._updateListVisibility(container);
    },

    _updateListVisibility(container) {
        const inputEl = container.querySelector("input.o_survey_upload_file");
        const listEl = container.querySelector(".o_survey_upload_list");
        if (!inputEl || !listEl) {
            return;
        }

        let newFileNames = [];
        try {
            newFileNames = JSON.parse(inputEl.dataset.oeFileName || "[]");
        } catch (_) {}

        const existingCount = (inputEl.dataset.existingIds || "")
            .split(",")
            .filter(Boolean).length;
        const totalCount = existingCount + newFileNames.length;

        let deleteAllBtn = container.querySelector(".o_survey_delete_all_btn");
        if (totalCount >= 2) {
            if (!deleteAllBtn) {
                deleteAllBtn = document.createElement("button");
                deleteAllBtn.type = "button";
                deleteAllBtn.className = "btn btn-sm btn-outline-secondary o_survey_delete_all_btn mt-1";
                deleteAllBtn.textContent = "Delete All";
                listEl.appendChild(deleteAllBtn);
            }
        } else if (deleteAllBtn) {
            deleteAllBtn.remove();
        }
    },

    async submitForm(...args) {
        if (this._uploadFileReadPromises && this._uploadFileReadPromises.size) {
            await Promise.all(Array.from(this._uploadFileReadPromises));
        }
        return super.submitForm(...args);
    },
});
