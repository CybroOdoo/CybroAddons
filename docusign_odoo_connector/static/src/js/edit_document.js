/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { PdfViewerField } from "@web/views/fields/pdf_viewer/pdf_viewer_field";
import { useRef } from "@odoo/owl";

export class EditPdfViewerField extends PdfViewerField {
    setup() {
        super.setup();
        this.iframePdf = useRef("iframePdf");
        this.tabs1 = [];
        this.count = 0;
        this.orm = useService("orm");
    }

    onLoadSuccess() {
        super.onLoadSuccess?.();

        const email_count = [];
        if (this.props.record.data.email_id) {
            email_count.push(this.props.record.data.email_id.display_name);
        }

        const iFrameDoc = this.iframePdf.el?.contentWindow?.document;
        if (!iFrameDoc) return;

        iFrameDoc.querySelectorAll("*").forEach(el => {
            el.style.userSelect = "none";
        });

        const viewer = iFrameDoc.querySelector("#viewer");
        if (!viewer) return;

        viewer.addEventListener("dblclick", (e) => {
            let pageno;
            let rect_doc;

            const target = e.target;
            const parent = target.parentNode;

            if (parent && parent.classList.contains("textLayer")) {
                pageno = parent.parentNode?.dataset?.pageNumber;
                rect_doc = parent.getBoundingClientRect();
            } else if (parent) {
                pageno = parent.dataset?.pageNumber;
                rect_doc = target.getBoundingClientRect();
            }

            const values = ["<Select Fields>", "FullName", "Email", "Company", "Signature", "Text"];
            const select = document.createElement("select");
            select.name = "fields";

            const rect = viewer.getBoundingClientRect();
            const recipients_list = [...email_count];

            for (let i = 0; i < recipients_list.length; i++) {
                this.tabs1.push({
                    fullNameTabs: [],
                    signHereTabs: [],
                    emailTabs: [],
                    companyTabs: [],
                    textTabs: [],
                    dateSignedTabs: [],
                });

                for (const val of values) {
                    const option = document.createElement("option");
                    option.value = `${val} by ${recipients_list[i]}`;
                    option.textContent = `${val} by ${recipients_list[i]}`;
                    select.appendChild(option);
                }
            }

            const optionDate = document.createElement("option");
            optionDate.value = "Date";
            optionDate.textContent = "Date";
            select.appendChild(optionDate);

            select.style.cssText = "width:130px; position:absolute; z-index:999";

            const z = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const z_doc = e.clientX - rect_doc.left;
            const y_doc = e.clientY - rect_doc.top;

            select.style.left = `${z}px`;
            select.style.top = `${y}px`;

            // 🔴 FIXED PART STARTS HERE
            select.addEventListener("change", async () => {

                const data = {
                    xPosition: parseInt(z_doc),
                    yPosition: parseInt(y_doc),
                    tabLabel: parseInt(z_doc + y_doc),
                    documentId: "1",
                    pageNumber: pageno,
                };

                const [label, recipient] = select.value.split(" by ");

                for (let i = 0; i < recipients_list.length; i++) {
                    if (select.value === "Date") {
                        this.tabs1[i].dateSignedTabs.push(data);
                    }
                    if (recipients_list[i] === recipient) {
                        if (label === "FullName") this.tabs1[i].fullNameTabs.push(data);
                        else if (label === "Signature") this.tabs1[i].signHereTabs.push(data);
                        else if (label === "Email") this.tabs1[i].emailTabs.push(data);
                        else if (label === "Company") this.tabs1[i].companyTabs.push(data);
                        else if (label === "Text") this.tabs1[i].textTabs.push(data);
                    }
                }

                await this.props.record.update({ data: JSON.stringify(this.tabs1) });
                
                const wizardId = this.props.record.resId;

            });
            // 🔴 FIXED PART ENDS HERE

            viewer.appendChild(select);
        });
    }
}

EditPdfViewerField.template = "docusign_odoo_connector.EditPdfViewerField";

// Correct field registration
const basePdfViewerField = registry.category("fields").get("pdf_viewer");

registry.category("fields").add("edit_pdf_viewer", {
    ...basePdfViewerField,
    component: EditPdfViewerField,
});
