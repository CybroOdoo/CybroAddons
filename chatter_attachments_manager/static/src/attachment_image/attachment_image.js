/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { onWillUnmount } from "@odoo/owl";
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
        this.notification = useService("notification");
        // Track which attachment's context menu is open
        this.openMenuId = null;
        // Close menu on any outside click
        this._onDocClick = (ev) => {
            if (!ev.target.closest(".am-cog-btn") && !ev.target.closest(".context_menu_dropdown")) {
                this.closeMenu();
            }
        };
        document.addEventListener("click", this._onDocClick);
        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocClick);
            this.closeMenu();
        });
    },

    notify(message, type = "warning") {
        if (this.notification) {
            this.notification.add(message, { type });
        } else if (this.env.services?.notification) {
            this.env.services.notification.add(message, { type });
        }
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
                title: _t("Edit Record"), desc: _t("Open in form view"),
                fn: (e) => { e.stopPropagation(); self.onClickEditImgRecord(e, attachment); self.closeMenu(); },
            },
            {
                icon: "fa-magic", iconClass: "am-ctx-icon--editor",
                title: _t("Image Editor"), desc: _t("Crop, annotate & adjust"),
                fn: (e) => { e.stopPropagation(); self.onClickImageEdit(e, attachment); self.closeMenu(); },
            },
            {
                icon: "fa-eye", iconClass: "am-ctx-icon--preview",
                title: _t("Preview Offline"), desc: _t("Open without internet"),
                fn: (e) => { e.stopPropagation(); self._onClickPreviewOfflineDirect(attachment, ext); self.closeMenu(); },
            },
            {
                icon: "fa-qrcode", iconClass: "am-ctx-icon--qr",
                title: _t("QR Code"), desc: _t("Generate download QR"),
                fn: (e) => { e.stopPropagation(); self._onClickQrCodeDirect(attachment); self.closeMenu(); },
            },
            {
                icon: "fa-trash", iconClass: "am-ctx-icon--delete",
                title: _t("Delete"), desc: _t("Remove this attachment"),
                extra: "am-ctx-item--danger divider-before",
                fn: (e) => { e.stopPropagation(); self.onClickUnlink(attachment); self.closeMenu(); },
            },
        ];

        // Build menu DOM safely using textContent
        floatingMenu.replaceChildren();
        actions.forEach((a) => {
            if (a.extra && a.extra.includes("divider-before")) {
                const divider = document.createElement("div");
                divider.className = "am-ctx-divider";
                floatingMenu.appendChild(divider);
            }
            const item = document.createElement("div");
            const extraClass = (a.extra || "").replace("divider-before", "").trim();
            item.className = `am-ctx-item ${extraClass}`;

            const iconSpan = document.createElement("span");
            iconSpan.className = `am-ctx-icon ${a.iconClass}`;
            const iconI = document.createElement("i");
            iconI.className = `fa ${a.icon}`;
            iconSpan.appendChild(iconI);

            const textSpan = document.createElement("span");
            textSpan.className = "am-ctx-text";
            const titleSpan = document.createElement("span");
            titleSpan.className = "am-ctx-title";
            titleSpan.textContent = a.title;
            const descSpan = document.createElement("span");
            descSpan.className = "am-ctx-desc";
            descSpan.textContent = a.desc;
            textSpan.appendChild(titleSpan);
            textSpan.appendChild(descSpan);

            item.appendChild(iconSpan);
            item.appendChild(textSpan);
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

    /**
     * Open window to edit image record
     */
    async onClickEditImgRecord(ev, attachment) {
        ev.stopPropagation();
        ev.preventDefault();
        markEventHandled(ev, 'AttachmentImage.onClickEditImgRecord');
        const self = this;
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
                try {
                    const orm = self.orm || self.env.services?.orm;
                    if (!orm) {
                        return;
                    }
                    const attachmentsData = await orm.read(
                        "ir.attachment",
                        [attachment.id],
                        [
                            "name",
                            "mimetype",
                            "file_size",
                            "checksum",
                            "res_model",
                            "res_id",
                            "access_token",
                            "description",
                        ],
                        { load: false }
                    );
                    if (attachmentsData && attachmentsData.length > 0) {
                        const updated = attachmentsData[0];
                        const updateVals = {
                            id: attachment.id,
                            name: updated.name,
                            mimetype: updated.mimetype,
                            file_size: updated.file_size,
                            checksum: updated.checksum,
                            extension: updated.name ? updated.name.split(".").pop().toLowerCase() : "",
                        };
                        if (updated.access_token) {
                            updateVals.access_token = updated.access_token;
                        }

                        // 1. Update mail store model
                        const store = self.store || self.env.services?.["mail.store"];
                        if (store) {
                            store.insert({ "ir.attachment": updateVals });
                        }
                        if (typeof attachment.update === "function") {
                            attachment.update(updateVals);
                        }

                        // 2. Directly update reactive properties on attachment record
                        attachment.name = updated.name;
                        if (updated.name) {
                            attachment.extension = updated.name.split(".").pop().toLowerCase();
                        }
                        if (updated.mimetype) {
                            attachment.mimetype = updated.mimetype;
                        }
                        if (updated.checksum) {
                            attachment.checksum = updated.checksum;
                        }
                        if (updated.file_size !== undefined && updated.file_size !== false) {
                            attachment.file_size = updated.file_size;
                        }
                        if (updated.access_token) {
                            attachment.access_token = updated.access_token;
                        }

                        // 3. Cache-bust <img> tags in DOM if thumbnail or image changed
                        const imgSelector = `img[src*="/web/image/${attachment.id}"], img[src*="/web/content/${attachment.id}"]`;
                        document.querySelectorAll(imgSelector).forEach((img) => {
                            const baseSrc = img.src.split('?')[0];
                            img.src = `${baseSrc}?unique=${encodeURIComponent(updated.checksum || Date.now())}&t=${Date.now()}`;
                        });
                    } else {
                        // Record was deleted in form dialog
                        if (typeof attachment.delete === "function") {
                            attachment.delete();
                        }
                    }
                } catch {
                    // Suppress refresh errors gracefully
                }

                // 4. Force re-render of AttachmentList component
                if (typeof self.render === "function") {
                    self.render();
                }

                // 5. Trigger thread / chatter updates
                if (attachment.thread?.fetchNewMessages) {
                    await attachment.thread.fetchNewMessages();
                }
                if (typeof self.hasParentReloadOnAttachmentsChanged === "boolean" && self.hasParentReloadOnAttachmentsChanged) {
                    self.reloadParentView();
                }
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
     * Open a window to edit image
     */
    async onClickImageEdit(ev, attachment) {
        const self = this;
        markEventHandled(ev, 'AttachmentImage.onClickImageEdit');

        if (typeof tui === "undefined" || !tui.ImageEditor) {
            this.notify(_t("Toast UI Image Editor library failed to load."), "danger");
            return;
        }

        // Check if file is an editable image
        const ext = (attachment.name || "").split(".").pop().toLowerCase();
        const isImg = attachment.isImage
            || ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp", "ico"].includes(ext)
            || (attachment.mimetype && attachment.mimetype.startsWith("image/"));
        if (!isImg) {
            this.notify(_t("This file cannot be edited in the image editor."), "warning");
            return;
        }

        // Remove any stale editor overlay from a previous open
        const staleOverlay = document.getElementById('am-img-editor-overlay');
        if (staleOverlay) { staleOverlay.remove(); }

        // ── Build a full-viewport overlay on <body> so TUI gets real dimensions ──
        const overlay = document.createElement('div');
        overlay.id = 'am-img-editor-overlay';
        overlay.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'right:0', 'bottom:0',
            'width:100%', 'height:100%', 'z-index:100000',
            'background:#1a1a1a', 'overflow:hidden', 'margin:0', 'padding:0',
        ].join(';');

        // Inner canvas wrapper — TUI is mounted here
        const editorMount = document.createElement('div');
        editorMount.id = 'am-tui-mount';
        editorMount.style.cssText = 'position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;overflow:hidden;margin:0;padding:0;';
        overlay.appendChild(editorMount);

        // Loading spinner indicator while image binary is fetched
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'am-img-editor-loading';
        loadingDiv.style.cssText = 'position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#fff;font-size:15px;z-index:100001;display:flex;align-items:center;gap:10px;background:rgba(0,0,0,0.7);padding:14px 24px;border-radius:8px;';
        const spinIcon = document.createElement('i');
        spinIcon.className = 'fa fa-circle-o-notch fa-spin fa-lg';
        const spinText = document.createElement('span');
        spinText.textContent = _t('Loading image…');
        loadingDiv.appendChild(spinIcon);
        loadingDiv.appendChild(spinText);
        overlay.appendChild(loadingDiv);

        // Append to body BEFORE init so dimensions are valid
        document.body.appendChild(overlay);

        // ── Fetch image data as a local base64 Data URL to prevent CORS/null errors ──
        let dataUrl = null;
        try {
            const resp = await fetch(`/web/content/${attachment.id}`);
            if (resp.ok) {
                const blob = await resp.blob();
                dataUrl = await new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                });
            }
        } catch (_) {}

        if (!dataUrl) {
            dataUrl = (this.getImageUrl ? this.getImageUrl(attachment) : null)
                || attachment.defaultSource
                || `/web/image/${attachment.id}`;
        }

        // ── Ensure Fabric compatibility across all versions ──
        if (window.fabric) {
            // Guard Canvas.setBackgroundImage callback against context/null errors.
            // NOTE: we wrap in try/catch instead of touching `this.backgroundImage`
            // because TUI's minified Fabric may call the callback without a bound
            // canvas `this`, causing "Cannot read properties of undefined (reading
            // 'backgroundImage')" in strict mode.
            if (window.fabric.Canvas && !window.fabric.Canvas.prototype._amPatchedSetBackgroundImage) {
                const origSetBackgroundImage = window.fabric.Canvas.prototype.setBackgroundImage;
                window.fabric.Canvas.prototype.setBackgroundImage = function (image, callback, options) {
                    const safeCallback = callback ? function () {
                        try {
                            return callback.apply(this, arguments);
                        } catch (_err) {
                            // Swallow fabric internal errors silently;
                            // the base64 pre-fetch already prevents null backgroundImage.
                        }
                    } : callback;
                    return origSetBackgroundImage.call(this, image, safeCallback, options);
                };
                window.fabric.Canvas.prototype._amPatchedSetBackgroundImage = true;
            }

            const majorVer = window.fabric.version ? parseInt(window.fabric.version.split('.')[0], 10) : 1;
            if (majorVer >= 2) {
                if (window.fabric.Image && window.fabric.Image.prototype.applyFilters) {
                    const origApplyFilters = window.fabric.Image.prototype.applyFilters;
                    window.fabric.Image.prototype.applyFilters = function (callback, filters) {
                        if (typeof callback === "function") {
                            const actualFilters = Array.isArray(filters) ? filters : this.filters;
                            try {
                                origApplyFilters.call(this, actualFilters);
                            } catch (_) {}
                            callback.call(this);
                            return this;
                        }
                        return origApplyFilters.apply(this, arguments);
                    };
                }
                if ('enableGLFiltering' in window.fabric) {
                    window.fabric.enableGLFiltering = false;
                }
                const F = window.fabric.Image.filters;
                if (F) {
                    if (!F.Sepia2 && F.Sepia) { F.Sepia2 = F.Sepia; }
                    if (!F.Tint && (F.BlendColor || F.BaseFilter)) { F.Tint = F.BlendColor || F.BaseFilter; }
                    if (!F.Multiply && (F.BlendColor || F.BaseFilter)) { F.Multiply = F.BlendColor || F.BaseFilter; }
                    if (!F.ColorFilter && (F.BlendColor || F.BaseFilter)) { F.ColorFilter = F.BlendColor || F.BaseFilter; }
                }
            }
        }

        // ── Initialise Toast UI Image Editor ──
        const availWidth = Math.max(window.innerWidth - 60, 300);
        const availHeight = Math.max(window.innerHeight - 280, 160);

        let imageEditor;
        try {
            imageEditor = new tui.ImageEditor(editorMount, {
                includeUI: {
                    loadImage: {
                        path: dataUrl,
                        name: attachment.name || 'Image',
                    },
                    initMenu: 'filter',
                    menuBarPosition: 'bottom',
                },
                cssMaxWidth: availWidth,
                cssMaxHeight: availHeight,
                usageStatistics: false,
            });
        } catch (err) {
            overlay.remove();
            this.notify(_t("Could not initialize image editor: %(error)s", { error: err?.message || err || "" }), "danger");
            return;
        }

        // Remove loading indicator once editor initialized
        if (loadingDiv && loadingDiv.parentNode) {
            loadingDiv.remove();
        }

        // ── Inject uniform button stylesheet into the overlay ──
        const editorStyle = document.createElement('style');
        editorStyle.textContent = `
            .tui-image-editor-header-buttons {
                display: inline-flex !important;
                align-items: center !important;
                gap: 8px !important;
            }
            .tui-image-editor-header-buttons button,
            .tui-image-editor-save-btn,
            .tui-image-editor-close-btn {
                position: relative !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: auto !important;
                min-width: 90px !important;
                height: 38px !important;
                line-height: 36px !important;
                padding: 0 20px !important;
                background: #ffffff !important;
                background-color: #ffffff !important;
                border: 1px solid #d1d5db !important;
                border-radius: 6px !important;
                color: #1f2937 !important;
                font-family: inherit !important;
                font-size: 13px !important;
                font-weight: 600 !important;
                letter-spacing: .02em !important;
                cursor: pointer !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
                transition: background-color .15s ease, border-color .15s ease, box-shadow .15s ease !important;
                outline: none !important;
                margin: 0 !important;
                vertical-align: middle !important;
            }
            .tui-image-editor-header-buttons button:hover,
            .tui-image-editor-save-btn:hover,
            .tui-image-editor-close-btn:hover {
                background: #f9fafb !important;
                background-color: #f9fafb !important;
                border-color: #9ca3af !important;
                color: #111827 !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
                filter: none !important;
                transform: none !important;
            }
            .tui-image-editor-header-buttons button:active,
            .tui-image-editor-save-btn:active,
            .tui-image-editor-close-btn:active {
                background: #f3f4f6 !important;
                background-color: #f3f4f6 !important;
                border-color: #6b7280 !important;
            }
            .tui-image-editor-save-btn:disabled {
                opacity: .55 !important;
                cursor: not-allowed !important;
                box-shadow: none !important;
            }
        `;
        overlay.appendChild(editorStyle);

        // ── Replace Download button with Save ──
        const downloadBtn = overlay.querySelector(
            '.tui-image-editor-header-buttons .tui-image-editor-download-btn'
        );
        let saveBtn;
        if (downloadBtn) {
            saveBtn = document.createElement('button');
            saveBtn.className = 'tui-image-editor-save-btn';
            saveBtn.textContent = _t('Save');
            downloadBtn.replaceWith(saveBtn);
        } else {
            saveBtn = overlay.querySelector('.tui-image-editor-save-btn');
        }

        // ── Add Close button ──
        const headerButtons = overlay.querySelector('.tui-image-editor-header-buttons');
        if (headerButtons && !overlay.querySelector('.tui-image-editor-close-btn')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'tui-image-editor-close-btn';
            closeBtn.textContent = _t('Close');
            headerButtons.appendChild(closeBtn);
            closeBtn.addEventListener('click', () => {
                overlay.remove();
            });
        }

        // ── Save handler ──
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                let myImage;
                try {
                    myImage = imageEditor.toDataURL();
                } catch (err) {
                    self.notify(_t("Failed to export image: %(error)s", { error: err?.message || err || "" }), "danger");
                    return;
                }
                if (!myImage) {
                    self.notify(_t("No image data to save."), "danger");
                    return;
                }

                saveBtn.disabled = true;
                const originalText = saveBtn.textContent;
                saveBtn.textContent = _t("Saving…");

                try {
                    const res = await self.orm.call(
                        'ir.attachment', 'save_edited_image',
                        [attachment.id, myImage]
                    );
                    overlay.remove();
                    self.notify(_t("Image saved successfully."), "success");

                    // 1. Update attachment checksum in the mail store model
                    const newChecksum = (res && res.checksum) || Date.now().toString();
                    if (typeof attachment.update === "function") {
                        attachment.update({ checksum: newChecksum });
                    }

                    // 2. Cache-bust all matching <img> tags in the DOM
                    const imgSelector = `img[src*="/web/image/${attachment.id}"], img[src*="/web/content/${attachment.id}"]`;
                    document.querySelectorAll(imgSelector).forEach((img) => {
                        const baseSrc = img.src.split('?')[0];
                        img.src = `${baseSrc}?unique=${encodeURIComponent(newChecksum)}&t=${Date.now()}`;
                    });

                    // 3. Trigger thread / chatter updates
                    if (attachment.thread?.fetchNewMessages) {
                        await attachment.thread.fetchNewMessages();
                    }
                    if (self.props.record?.fetchNewMessages) {
                        await self.props.record.fetchNewMessages();
                    }
                    if (typeof self.hasParentReloadOnAttachmentsChanged === "boolean" && self.hasParentReloadOnAttachmentsChanged) {
                        self.reloadParentView();
                    }
                } catch (err) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = originalText;
                    self.notify(_t("Error saving edited image: %(error)s", { error: err?.message || err || "" }), "danger");
                }
            });
        }
    },

    /**
     * Preview Offline — builds its own floating modal safely using textContent.
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

        // Header — safe textContent to prevent XSS
        const header = document.createElement("div");
        header.style.cssText = "display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid #e5e7eb;";
        const titleSpan = document.createElement("span");
        titleSpan.style.cssText = "font-weight:600;font-size:14px;color:#111;";
        titleSpan.textContent = attachment.name || "";
        header.appendChild(titleSpan);

        const closeBtn = document.createElement("button");
        closeBtn.id = "am-preview-close";
        closeBtn.style.cssText = "background:none;border:none;font-size:20px;cursor:pointer;color:#6b7280;";
        closeBtn.textContent = "×";
        header.appendChild(closeBtn);
        box.appendChild(header);

        // Content area
        const content = document.createElement("div");
        content.style.cssText = "flex:1;overflow:auto;padding:16px;";
        const loadingP = document.createElement("p");
        loadingP.style.cssText = "color:#6b7280;font-size:13px;";
        loadingP.textContent = _t("Loading preview…");
        content.appendChild(loadingP);
        box.appendChild(content);
        overlay.appendChild(box);
        document.body.appendChild(overlay);

        // Close button
        closeBtn.onclick = () => overlay.remove();
        overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); } };

        try {
            if (["xls", "xlsx", "docx"].includes(ext)) {
                const data = await this.orm.call("ir.attachment", "decode_content", [attachment.id, ext]);
                content.replaceChildren();
                if (typeof data === "string") {
                    const msg = document.createElement("p");
                    msg.style.cssText = "color:#6b7280;text-align:center;padding:24px;";
                    msg.textContent = data;
                    content.appendChild(msg);
                } else if ((ext === "xlsx" || ext === "xls") && data && data.content) {
                    const parser = new DOMParser();
                    const parsedDoc = parser.parseFromString(data.content, "text/html");
                    const table = parsedDoc.querySelector("table");
                    if (table) {
                        table.style.cssText = "border-collapse:collapse;width:100%;font-size:13px;";
                        table.querySelectorAll("th,td").forEach(cell => {
                            cell.style.cssText = "border:1px solid #d1d5db;padding:6px 10px;text-align:left;";
                        });
                        const tableWrapper = document.createElement("div");
                        tableWrapper.style.cssText = "overflow:auto;";
                        tableWrapper.appendChild(table);
                        content.appendChild(tableWrapper);
                    }
                } else if (ext === "docx" && data && Array.isArray(data.content)) {
                    for (const para of data.content) {
                        const p = document.createElement("p");
                        p.textContent = para;
                        p.style.cssText = "margin:0 0 8px;font-size:14px;line-height:1.6;color:#111;";
                        content.appendChild(p);
                    }
                }
            } else if (ext === "pdf" || attachment.mimetype === "application/pdf") {
                const pdfUrl = attachment.defaultSource || `/web/content/${attachment.id}/${encodeURIComponent(attachment.name)}`;
                content.style.cssText = "flex:1;padding:0;height:70vh;";
                const iframe = document.createElement("iframe");
                iframe.src = pdfUrl;
                iframe.style.cssText = "width:100%;height:70vh;border:none;";
                iframe.title = attachment.name || "";
                content.replaceChildren(iframe);
            } else if (attachment.isImage || ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp", "ico"].includes(ext) || (attachment.mimetype && attachment.mimetype.startsWith("image/"))) {
                const imgUrl = (this.getImageUrl ? this.getImageUrl(attachment) : null)
                    || attachment.defaultSource
                    || `/web/image/${attachment.id}`;
                content.style.cssText = "flex:1;display:flex;align-items:center;justify-content:center;background:#18181b;padding:20px;overflow:auto;min-height:300px;max-height:75vh;";
                const img = document.createElement("img");
                img.src = imgUrl;
                img.style.cssText = "max-width:100%;max-height:70vh;object-fit:contain;border-radius:6px;box-shadow:0 10px 25px rgba(0,0,0,0.5);";
                img.alt = attachment.name || "";
                content.replaceChildren(img);
            } else if (attachment.isVideo || ["mp4", "webm", "ogg"].includes(ext) || (attachment.mimetype && attachment.mimetype.startsWith("video/"))) {
                const videoUrl = attachment.defaultSource || `/web/content/${attachment.id}/${encodeURIComponent(attachment.name)}`;
                content.style.cssText = "flex:1;display:flex;align-items:center;justify-content:center;background:#000;padding:16px;max-height:75vh;";
                const video = document.createElement("video");
                video.controls = true;
                video.autoplay = true;
                video.style.cssText = "max-width:100%;max-height:70vh;";
                video.src = videoUrl;
                content.replaceChildren(video);
            } else if (attachment.isAudio || ["mp3", "wav", "ogg"].includes(ext) || (attachment.mimetype && attachment.mimetype.startsWith("audio/"))) {
                const audioUrl = attachment.defaultSource || `/web/content/${attachment.id}/${encodeURIComponent(attachment.name)}`;
                content.style.cssText = "flex:1;display:flex;align-items:center;justify-content:center;padding:32px;";
                const audio = document.createElement("audio");
                audio.controls = true;
                audio.autoplay = true;
                audio.style.cssText = "width:80%;";
                audio.src = audioUrl;
                content.replaceChildren(audio);
            } else if (attachment.isText || ["txt", "csv", "log", "json", "xml", "md", "html"].includes(ext)) {
                const textUrl = attachment.defaultSource || `/web/content/${attachment.id}/${encodeURIComponent(attachment.name)}`;
                content.style.cssText = "flex:1;padding:0;height:70vh;";
                const iframe = document.createElement("iframe");
                iframe.src = textUrl;
                iframe.style.cssText = "width:100%;height:70vh;border:none;";
                iframe.title = attachment.name || "";
                content.replaceChildren(iframe);
            } else {
                const notAvailP = document.createElement("p");
                notAvailP.style.cssText = "color:#ef4444;";
                notAvailP.textContent = _t("Preview not available for this file type (%(ext)s).", { ext });
                content.replaceChildren(notAvailP);
            }
        } catch (err) {
            const errP = document.createElement("p");
            errP.style.cssText = "color:#ef4444;";
            errP.textContent = _t("Error loading preview: %(error)s", { error: err ? err.message || err : "" });
            content.replaceChildren(errP);
        }
    },

    /**
     * QR Code — calls generate_qr_code and passes the returned data dict
     * directly to the QWeb PDF report via doAction.
     */
    async _onClickQrCodeDirect(attachment) {
        const data = await this.orm.call("ir.attachment", "generate_qr_code", [attachment.id]);
        if (!data || !data.image) {
            this.notify(_t("QR code generation failed."), "danger");
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
});
