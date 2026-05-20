/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AttachmentList } from "@mail/core/common/attachment_list";
import { isEventHandled, markEventHandled } from "@web/core/utils/misc";
import { useService } from "@web/core/utils/hooks";


patch(AttachmentList.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        // Track which attachment's context menu is open
        this.openMenuId = null;
        // Close menu on any outside click
        this._onDocClick = (ev) => {
            if (!ev.target.closest(".am-cog-btn") && !ev.target.closest(".context_menu_dropdown")) {
                this.openMenuId = null;
                this._syncMenuVisibility();
            }
        };
        document.addEventListener("click", this._onDocClick);
    },

    /** Toggle the context menu for one attachment */
    onClickCogBtn(ev, attachment) {
        ev.stopPropagation();

        // Close if already open for same attachment
        if (this.openMenuId === attachment.id) {
            this.closeMenu();
            return;
        }

        // Use a singleton fixed-position floating menu on <body>
        let floatingMenu = document.getElementById("am-floating-ctx-menu");
        if (!floatingMenu) {
            floatingMenu = document.createElement("div");
            floatingMenu.id = "am-floating-ctx-menu";
            floatingMenu.className = "context_menu_dropdown am-ctx-menu";
            document.body.appendChild(floatingMenu);
        }

        const self = this;
        // Derive file extension from the attachment name (e.g. "report.pdf" → "pdf")
        const ext = (attachment.name || "").split(".").pop().toLowerCase();

        // All five menu actions — divider is placed before Delete
        const actions = [
            {
                icon: "fa-pencil", iconClass: "am-ctx-icon--edit",
                title: "Edit Record", desc: "Open in form view",
                fn: (e) => { e.stopPropagation(); self.onClickEditImgRecord(e, attachment); self.closeMenu(); },
            },
            {
                icon: "fa-magic", iconClass: "am-ctx-icon--editor",
                title: "Image Editor", desc: "Crop, annotate & adjust",
                fn: (e) => { e.stopPropagation(); self.onClickImageEdit(e, attachment); self.closeMenu(); },
            },
            {
                icon: "fa-eye", iconClass: "am-ctx-icon--preview",
                title: "Preview Offline", desc: "Open without internet",
                fn: (e) => { e.stopPropagation(); self._onClickPreviewOfflineDirect(attachment, ext); self.closeMenu(); },
            },
            {
                icon: "fa-qrcode", iconClass: "am-ctx-icon--qr",
                title: "QR Code", desc: "Generate download QR",
                fn: (e) => { e.stopPropagation(); self._onClickQrCodeDirect(attachment); self.closeMenu(); },
            },
            {
                icon: "fa-trash", iconClass: "am-ctx-icon--delete",
                title: "Delete", desc: "Remove this attachment",
                extra: "am-ctx-item--danger divider-before",
                fn: (e) => { e.stopPropagation(); self.onClickUnlink(attachment); self.closeMenu(); },
            },
        ];

        // Build menu DOM in a single pass
        floatingMenu.innerHTML = "";
        actions.forEach((a) => {
            if (a.extra && a.extra.includes("divider-before")) {
                const divider = document.createElement("div");
                divider.className = "am-ctx-divider";
                floatingMenu.appendChild(divider);
            }
            const item = document.createElement("div");
            const extraClass = (a.extra || "").replace("divider-before", "").trim();
            item.className = `am-ctx-item ${extraClass}`;
            item.innerHTML = `
                <span class="am-ctx-icon ${a.iconClass}"><i class="fa ${a.icon}"></i></span>
                <span class="am-ctx-text">
                    <span class="am-ctx-title">${a.title}</span>
                    <span class="am-ctx-desc">${a.desc}</span>
                </span>`;
            item.onclick = a.fn;
            floatingMenu.appendChild(item);
        });

        floatingMenu.style.display = "block";

        // Position right below the ⋮ button using viewport coords
        const btn = ev.currentTarget;
        const rect = btn.getBoundingClientRect();
        const menuWidth = 225;
        let left = rect.left;
        if (left + menuWidth > window.innerWidth - 8) {
            left = rect.right - menuWidth;
        }
        floatingMenu.style.position = "fixed";
        floatingMenu.style.top = (rect.bottom + 4) + "px";
        floatingMenu.style.left = left + "px";
        floatingMenu.style.zIndex = "99999";

        this.openMenuId = attachment.id;

        // Register a one-time outside-click listener
        if (!this._outsideClickBound) {
            this._outsideClickBound = true;
            document.addEventListener("click", (e) => {
                if (!e.target.closest(".am-cog-btn") && !e.target.closest("#am-floating-ctx-menu")) {
                    self.closeMenu();
                }
            });
        }
    },

    /** Close the floating context menu */
    closeMenu() {
        this.openMenuId = null;
        const menu = document.getElementById("am-floating-ctx-menu");
        if (menu) {
            menu.style.display = "none";
            menu.classList.remove("am-ctx-open");
        }
    },

    /** No-op kept for compatibility (floating menu is managed directly) */
    _syncMenuVisibility() { },
    /**
     Open window to edit image record
   **/
    async onClickEditImgRecord(ev, attachment) {
        ev.stopPropagation();
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        await this.env.services.action.doAction({
            name: _t("Attachment"),
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment.id,
            res_model: 'ir.attachment',
            context: { create: false },
        }, {
            onClose: async () => {
                await location.reload();
            },
        });
    },

    onClickImage(ev) {
        if (isEventHandled(ev, 'onClickEditImgRecord')) {
            return;
        }
        if (isEventHandled(ev, 'onClickImageEdit')) {
            return;
        }
        return super.onClickImage(...arguments);
    },

    /**
    Open a window to edit image
   **/
    async onClickImageEdit(ev, attachment) {
        var self = this;
        markEventHandled(ev, 'AttachmentImage.onClickImageEdit');

        if (typeof tui === "undefined" || !tui.ImageEditor) {
            console.error("Toast UI Image Editor library (tui) failed to load.");
            alert(_t("Toast UI Image Editor library failed to load. Please check your internet connection or CDN availability."));
            return;
        }

        // Show the editor container first so tui has valid offsetWidth/offsetHeight to draw on
        const editorContainer = document.querySelector('#imageEditor_' + attachment.id);
        if (editorContainer) {
            editorContainer.style.display = 'block';
        }

        // Initialize the image editor on the unique container ID
        var imageEditor = new tui.ImageEditor('#tui-image-editor-container_' + attachment.id, {
            includeUI: {
                loadImage: {
                    path: "/web/image/ir.attachment/" + attachment.id + "/datas",
                    name: attachment.name || 'SampleImage'
                },
                imageSize: {
                    oldWidth: "0",
                    oldHeight: "0",
                    newWidth: "300",
                    newHeight: "90"
                },
                initMenu: 'filter',
                menuBarPosition: 'bottom'
            },
            cssMaxWidth: 500,
            cssMaxHeight: 590,
            usageStatistics: false
        });

        // Scope element queries to the container of this card
        const cardEl = editorContainer;

        // Replace the download button with a save button
        const downloadButton = cardEl.querySelector('.tui-image-editor-header-buttons .tui-image-editor-download-btn');
        if (downloadButton) {
            const saveButton = document.createElement('button');
            saveButton.classList.add('tui-image-editor-save-btn');
            saveButton.textContent = 'Save';
            downloadButton.replaceWith(saveButton);
        }

        // Add a close button to the header
        const headerButtons = cardEl.querySelector('.tui-image-editor-header-buttons');
        if (headerButtons) {
            const closeButton = document.createElement('div');
            closeButton.classList.add('tui-image-editor-close-btn');
            closeButton.textContent = 'Close';
            closeButton.style.cssText = `
            background-color: #fff;
            border: 1px solid #ddd;
            color: #222;
            font-family: sans-serif;
            font-size: 12px;
            padding: 5px;
            cursor: pointer;
        `;
            headerButtons.appendChild(closeButton);

            // Add event listener for the close button
            closeButton.addEventListener('click', () => {
                this.CloseImageEditor(attachment.id);
            });
        }

        // Add event listener for the save button
        const saveButton = cardEl.querySelector('.tui-image-editor-save-btn');
        if (saveButton) {
            saveButton.addEventListener('click', async () => {
                const myImage = imageEditor.toDataURL();
                const attachment_id = attachment.id;
                try {
                    await self.orm.call("ir.attachment", "save_edited_image", [attachment_id, myImage]);
                    location.reload(); // Reload the page after saving
                } catch (error) {
                    console.error("Error saving edited image:", error);
                }
            });
        }
    },

    CloseImageEditor: function (attachmentId) {
        const editorContainer = document.getElementById("imageEditor_" + attachmentId);
        if (editorContainer) {
            editorContainer.style.display = "none";
        }
    },

    /**
     * Records can be edited by altering the file name and adding tags.
     */
    async onClickEditRecord(ev, attachment) {
        ev.stopPropagation();
        ev.preventDefault();
        await this.env.services.action.doAction({
            name: _t("Attachment"),
            type: 'ir.actions.act_window',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: attachment.id,
            res_model: 'ir.attachment',
            context: { create: false },
        }, {
            onClose: async () => {
                await location.reload();
            },
        });
    },

    /**
     * Preview Offline — builds its own floating modal so no external HTML element is needed.
     */
    async _onClickPreviewOfflineDirect(attachment, ext) {
        // Remove any previous preview popup
        const old = document.getElementById("am-preview-popup");
        if (old) { old.remove(); }

        const overlay = document.createElement("div");
        overlay.id = "am-preview-popup";
        overlay.style.cssText = [
            "position:fixed", "inset:0", "z-index:100000",
            "background:rgba(0,0,0,.55)", "display:flex",
            "align-items:center", "justify-content:center",
        ].join(";");

        const box = document.createElement("div");
        box.style.cssText = [
            "background:#fff", "border-radius:10px", "width:80vw", "max-height:85vh",
            "display:flex", "flex-direction:column", "overflow:hidden",
            "box-shadow:0 20px 60px rgba(0,0,0,.4)",
        ].join(";");

        // Header
        const header = document.createElement("div");
        header.style.cssText = "display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #e5e7eb;";
        header.innerHTML = `
            <span style="font-weight:600;font-size:14px;color:#111;">${attachment.name}</span>
            <button id="am-preview-close" style="background:none;border:none;font-size:20px;cursor:pointer;color:#6b7280;">&times;</button>`;
        box.appendChild(header);

        // Content area
        const content = document.createElement("div");
        content.style.cssText = "flex:1;overflow:auto;padding:16px;";
        content.innerHTML = `<p style="color:#6b7280;font-size:13px;">Loading preview…</p>`;
        box.appendChild(content);
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        // Close button
        overlay.querySelector("#am-preview-close").onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); } };

        try {
            if (["xls", "xlsx", "docx"].includes(ext)) {
                const data = await this.orm.call("ir.attachment", "decode_content", [attachment.id, ext]);
                content.innerHTML = "";
                if (ext === "xlsx" || ext === "xls") {
                    content.innerHTML = `<div style="overflow:auto;">${data}</div>`;
                    const table = content.querySelector("table");
                    if (table) {
                        table.style.cssText = "border-collapse:collapse;width:100%;font-size:13px;";
                        table.querySelectorAll("th,td").forEach(cell => {
                            cell.style.cssText = "border:1px solid #d1d5db;padding:6px 10px;text-align:left;";
                        });
                    }
                } else if (ext === "docx") {
                    content.innerHTML = "";
                    for (const para of data) {
                        const p = document.createElement("p");
                        p.textContent = para;
                        p.style.cssText = "margin:0 0 8px;font-size:14px;line-height:1.6;color:#111;";
                        content.appendChild(p);
                    }
                }
            } else if (ext === "pdf" || attachment.mimetype === "application/pdf") {
                // Embed PDF in an iframe for offline-like view
                const pdfUrl = `/web/content/ir.attachment/${attachment.id}/datas/${encodeURIComponent(attachment.name)}`;
                content.style.cssText = "flex:1;padding:0;height:70vh;";
                content.innerHTML = `<iframe src="${pdfUrl}" style="width:100%;height:70vh;border:none;" title="${attachment.name}"></iframe>`;
            } else {
                content.innerHTML = `<p style="color:#ef4444;">Preview not available for this file type (<strong>${ext}</strong>).</p>`;
            }
        } catch (err) {
            content.innerHTML = `<p style="color:#ef4444;">Error loading preview: ${err.message || err}</p>`;
        }
    },

    /**
     * QR Code — calls generate_qr_code and passes the returned data dict
     * directly to the QWeb PDF report via doAction.
     */
    async _onClickQrCodeDirect(attachment) {
        const data = await this.orm.call("ir.attachment", "generate_qr_code", [attachment.id]);
        if (!data || !data.image) {
            console.error("QR code generation failed or returned empty data.");
            return;
        }
        await this.env.services.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "chatter_attachments_manager.attachment_qr_report_template",
            report_file: "chatter_attachments_manager.attachment_qr_report_template",
            data: data,
        });
    },


    /**
     * Offline Preview of file type 'docx', 'xlsx' and 'pdf'
    */
    async onClickPreviewOffline(ev, attachment) {
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        const type = ev.currentTarget?.dataset?.type;
        const modal = document.getElementById("xlsx_preview");
        if (!modal) {
            return;
        }
        const fileHead = modal.querySelector("#FileHead");
        if (fileHead) {
            fileHead.textContent = ev.target.name;
        }
        if (type === 'xls' || type === 'xlsx' || type === 'docx') {
            modal.style.display = "block";
            var preview = await this.orm.call
                ("ir.attachment", "decode_content", [parseInt(ev.target.id), type]).then(function (data) {
                    if (type === 'xls' || type === 'xlsx') {
                        const docs = modal.querySelector(".MyDocs");
                        const table = modal.querySelector(".XlsxTable");
                        if (docs) {
                            docs.textContent = "";
                        }
                        if (table) {
                            table.innerHTML = data;
                        }
                        const frame = modal.querySelector(".dataframe");
                        if (frame) {
                            frame.id = "MyTable";
                        }
                    }
                    else if (type === 'docx') {
                        const docs = modal.querySelector(".MyDocs");
                        if (docs) {
                            docs.textContent = "";
                            for (const para of data) {
                                const p = document.createElement("p");
                                p.textContent = para;
                                docs.appendChild(p);
                            }
                        }
                    }
                });
        }
        else {
            self.fileViewer.open(attachment, self.props.attachments)
        }
    },

    /**
  Close preview window
**/
    stopPreviewButton(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const modal = document.getElementById("xlsx_preview");
        if (modal) {
            modal.style.display = "none";
        }
    },

    /**
    * For generating Qr Code contain download link of attachment.
    */
    async _onClickQrCode(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        await this.orm.call
            ("ir.attachment", "generate_qr_code", [parseInt(ev.target.id)]).then(function (data) {
                var act = self.env.services.action.doAction({
                    type: 'ir.actions.report',
                    report_type: 'qweb-pdf',
                    report_name: 'chatter_attachments_manager.attachment_qr_report_template',
                    report_file: 'chatter_attachments_manager.attachment_qr_report_template',
                    data: data,
                });
            });
    },
});
