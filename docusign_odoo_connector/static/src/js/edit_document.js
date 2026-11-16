/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { PdfViewerField } from "@web/views/fields/pdf_viewer/pdf_viewer_field";
import { url } from "@web/core/utils/urls";
import { useOnChange } from "@odoo/owl";

export class EditPdfViewerField extends PdfViewerField {
    static template = "docusign_odoo_connector.EditPdfViewerField";

    get urlFile() {
        if (this.state.objectUrl) {
            return this.state.objectUrl;
        }
        const attachmentData = this.props.record.data.attachment_id;
        const attachmentId = attachmentData && (
            Array.isArray(attachmentData)
                ? attachmentData[0]
                : (typeof attachmentData === "object" ? attachmentData.id : attachmentData)
        );
        if (attachmentId) {
            return url(`/web/content/${attachmentId}`);
        }
        if (this.props.record.resId) {
            return url("/web/content", {
                model: this.props.record.resModel,
                field: this.props.name,
                id: this.props.record.resId,
            });
        }
        return super.urlFile;
    }

    setup() {
        super.setup();
        try {
            const rawPrefs = window.localStorage.getItem("pdfjs.preferences");
            const prefs = rawPrefs ? JSON.parse(rawPrefs) : {};
            prefs.enableScripting = false;
            prefs.enableAutoLinking = false;
            window.localStorage.setItem("pdfjs.preferences", JSON.stringify(prefs));
        } catch (e) {
            console.warn("Could not set pdfjs preferences:", e);
        }

        this.iframePdf = this.iframeViewerPdfRef;
        this.tabs1 = [];
        this.count = 0;
        this.orm = useService("orm");

        if (this.props.record.data.data) {
            try {
                this.tabs1 = JSON.parse(this.props.record.data.data);
            } catch {
                this.tabs1 = [];
            }
        }

        useOnChange(
            () => [this.iframeViewerPdfRef()],
            (iframe) => {
                if (iframe) {
                    const attach = () => this.initPdfViewerEvents();
                    iframe.addEventListener("load", attach);
                    if (iframe.contentDocument && iframe.contentDocument.readyState === "complete") {
                        attach();
                    }
                }
            }
        );
    }

    onLoadSuccess() {
        super.onLoadSuccess?.();
        this.initPdfViewerEvents();
    }

    initPdfViewerEvents() {
        const iframe = this.iframeViewerPdfRef ? this.iframeViewerPdfRef() : (this.iframePdf ? this.iframePdf() : null);
        if (!iframe) return;

        const iFrameDoc = iframe.contentDocument || iframe.contentWindow?.document;
        if (!iFrameDoc) return;

        // Add custom styles to prevent text selection from interfering with double-clicks
        if (!iFrameDoc.querySelector("#docusign-custom-style")) {
            const style = iFrameDoc.createElement("style");
            style.id = "docusign-custom-style";
            style.textContent = `
                #viewerContainer, #viewer, .page, .textLayer, .canvasWrapper {
                    user-select: none !important;
                    -webkit-user-select: none !important;
                }
                .docusign-field-select {
                    width: 150px;
                    position: absolute;
                    z-index: 9999;
                    background: #ffffff;
                    color: #000000;
                    border: 2px solid #000000;
                    border-radius: 4px;
                    padding: 2px 4px;
                    font-size: 12px;
                    font-weight: 500;
                    cursor: pointer;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                }
            `;
            if (iFrameDoc.head) {
                iFrameDoc.head.appendChild(style);
            }
        }

        const container = iFrameDoc.querySelector("#viewerContainer") || iFrameDoc.querySelector("#viewer");
        if (!container) return;

        if (container.dataset.docusignEventsAttached === "true") return;
        container.dataset.docusignEventsAttached = "true";

        const getPageScale = (pageno) => {
            const pdfApp = iframe.contentWindow?.PDFViewerApplication;
            const pageIdx = Math.max(0, parseInt(pageno, 10) - 1);
            const pageView = pdfApp?.pdfViewer?.getPageView?.(pageIdx);
            if (pageView?.viewport?.scale) {
                return pageView.viewport.scale;
            }
            return 96 / 72;
        };

        const handleDblClick = (e) => {
            if (e.target.tagName === "SELECT" || e.target.closest("select")) {
                return;
            }

            const pageEl = e.target.closest(".page") || iFrameDoc.querySelector(".page") || container;
            let pageno = "1";
            let rect_doc = pageEl.getBoundingClientRect();

            if (pageEl && pageEl.dataset && pageEl.dataset.pageNumber) {
                pageno = pageEl.dataset.pageNumber;
            } else if (pageEl && pageEl.getAttribute) {
                pageno = pageEl.getAttribute("data-page-number") || "1";
            }

            const z_doc = Math.round(e.clientX - rect_doc.left);
            const y_doc = Math.round(e.clientY - rect_doc.top);
            const pageScale = getPageScale(pageno);
            const pageWidthPt = rect_doc.width > 0 ? Math.round(rect_doc.width / pageScale) : 595;
            const pageHeightPt = rect_doc.height > 0 ? Math.round(rect_doc.height / pageScale) : 792;
            const pdfX = Math.max(0, Math.min(Math.round(z_doc / pageScale), Math.max(0, pageWidthPt - 180)));
            const pdfY = Math.max(0, Math.min(Math.round(y_doc / pageScale), Math.max(0, pageHeightPt - 50)));

            // Extract recipients from partner_names, partner_ids or email_id
            let recipients_list = [];
            const partnerNamesData = this.props.record.data.partner_names;
            if (partnerNamesData && typeof partnerNamesData === "string") {
                recipients_list = partnerNamesData.split(",").map((s) => s.trim()).filter(Boolean);
            }
            if (recipients_list.length === 0) {
                const partnerData = this.props.record.data.partner_ids;
                if (partnerData) {
                    if (partnerData.records && Array.isArray(partnerData.records)) {
                        recipients_list = partnerData.records
                            .map((r) => r.data.display_name || r.data.name)
                            .filter(Boolean);
                    } else if (Array.isArray(partnerData)) {
                        for (const item of partnerData) {
                            if (item && typeof item === "object") {
                                recipients_list.push(item.display_name || item.name || (item.data && (item.data.display_name || item.data.name)));
                            } else if (Array.isArray(item) && item.length > 1) {
                                recipients_list.push(item[1]);
                            }
                        }
                        recipients_list = recipients_list.filter(Boolean);
                    }
                }
            }
            if (recipients_list.length === 0) {
                let recipientName = "Signer";
                const emailData = this.props.record.data.email_id;
                if (emailData) {
                    if (Array.isArray(emailData) && emailData.length > 1) {
                        recipientName = emailData[1];
                    } else if (typeof emailData === "object" && (emailData.display_name || emailData.name)) {
                        recipientName = emailData.display_name || emailData.name;
                    } else if (typeof emailData === "string") {
                        recipientName = emailData;
                    }
                }
                recipients_list = [recipientName];
            }

            const values = ["FullName", "Email", "Company", "Signature", "Text"];
            const select = iFrameDoc.createElement("select");
            select.name = "fields";
            select.className = "docusign-field-select";

            const defaultOption = iFrameDoc.createElement("option");
            defaultOption.value = "";
            defaultOption.textContent = "<Select Fields>";
            select.appendChild(defaultOption);

            for (let i = 0; i < recipients_list.length; i++) {
                for (const val of values) {
                    const option = iFrameDoc.createElement("option");
                    option.value = `${val} by ${recipients_list[i]}`;
                    option.textContent = `${val} by ${recipients_list[i]}`;
                    select.appendChild(option);
                }
            }

            const optionDate = iFrameDoc.createElement("option");
            optionDate.value = "Date";
            optionDate.textContent = "Date";
            select.appendChild(optionDate);

            // Positioning relative to the page
            select.style.left = `${z_doc}px`;
            select.style.top = `${y_doc}px`;

            select.addEventListener("change", async () => {
                const selectedVal = select.value;
                if (!selectedVal || selectedVal.startsWith("<Select")) {
                    return;
                }

                const data = {
                    xPosition: pdfX,
                    yPosition: pdfY,
                    tabLabel: pdfX + pdfY,
                    documentId: "1",
                    pageNumber: pageno,
                };

                const [label, recipient] = selectedVal.split(" by ");

                if (!this.tabs1 || !Array.isArray(this.tabs1) || this.tabs1.length === 0) {
                    this.tabs1 = recipients_list.map((rec) => ({
                        recipient: rec,
                        fullNameTabs: [],
                        signHereTabs: [],
                        emailTabs: [],
                        companyTabs: [],
                        textTabs: [],
                        dateSignedTabs: [],
                    }));
                } else {
                    for (const rec of recipients_list) {
                        if (!this.tabs1.some((t) => t && t.recipient === rec)) {
                            this.tabs1.push({
                                recipient: rec,
                                fullNameTabs: [],
                                signHereTabs: [],
                                emailTabs: [],
                                companyTabs: [],
                                textTabs: [],
                                dateSignedTabs: [],
                            });
                        }
                    }
                }

                for (let i = 0; i < this.tabs1.length; i++) {
                    const tabEntry = this.tabs1[i];
                    if (!tabEntry) continue;
                    if (selectedVal === "Date") {
                        tabEntry.dateSignedTabs.push(data);
                    }
                    if (tabEntry.recipient === recipient || (!tabEntry.recipient && recipients_list[i] === recipient)) {
                        if (label === "FullName") tabEntry.fullNameTabs.push(data);
                        else if (label === "Signature") tabEntry.signHereTabs.push(data);
                        else if (label === "Email") tabEntry.emailTabs.push(data);
                        else if (label === "Company") tabEntry.companyTabs.push(data);
                        else if (label === "Text") tabEntry.textTabs.push(data);
                    }
                }

                await this.props.record.update({ data: JSON.stringify(this.tabs1) });
            });

            pageEl.appendChild(select);
            select.focus();
        };

        const renderExistingTabs = () => {
            if (!this.tabs1 || !Array.isArray(this.tabs1)) return;
            const pages = iFrameDoc.querySelectorAll(".page");
            for (let i = 0; i < this.tabs1.length; i++) {
                const tabEntry = this.tabs1[i];
                if (!tabEntry) continue;
                const rec = tabEntry.recipient || "";
                const tabTypes = [
                    { key: "fullNameTabs", label: "FullName" },
                    { key: "signHereTabs", label: "Signature" },
                    { key: "emailTabs", label: "Email" },
                    { key: "companyTabs", label: "Company" },
                    { key: "textTabs", label: "Text" },
                    { key: "dateSignedTabs", label: "Date" },
                ];
                for (const { key, label } of tabTypes) {
                    const tabs = tabEntry[key] || [];
                    for (const tab of tabs) {
                        const pageNum = tab.pageNumber || "1";
                        const pageEl =
                            iFrameDoc.querySelector(`.page[data-page-number="${pageNum}"]`) ||
                            pages[0] ||
                            container;
                        if (!pageEl) continue;

                        const pageScale = getPageScale(pageNum);
                        const badgeId = `tab-badge-${pageNum}-${tab.xPosition}-${tab.yPosition}-${label}`;
                        if (iFrameDoc.getElementById(badgeId)) continue;

                        const badge = iFrameDoc.createElement("div");
                        badge.id = badgeId;
                        badge.className = "docusign-field-select";
                        badge.style.position = "absolute";
                        badge.style.left = `${Math.round((tab.xPosition || 0) * pageScale)}px`;
                        badge.style.top = `${Math.round((tab.yPosition || 0) * pageScale)}px`;
                        badge.style.background = "#eff6ff";
                        badge.style.color = "#1e40af";
                        badge.style.borderColor = "#3b82f6";
                        badge.textContent = label === "Date" ? "Date" : `${label} by ${rec}`;
                        pageEl.appendChild(badge);
                    }
                }
            }
        };
        renderExistingTabs();

        container.addEventListener("dblclick", handleDblClick);
        const viewer = iFrameDoc.querySelector("#viewer");
        if (viewer && viewer !== container) {
            viewer.addEventListener("dblclick", handleDblClick);
        }
    }
}

EditPdfViewerField.template = "docusign_odoo_connector.EditPdfViewerField";

const basePdfViewerField = registry.category("fields").get("pdf_viewer");

registry.category("fields").add("edit_pdf_viewer", {
    ...basePdfViewerField,
    component: EditPdfViewerField,
});
