/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";


class PosReceiptLayoutClientAction extends Component {
    static template = "custom_receipt_for_pos.client_layout_customisation_template";


    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.receiptContentRef = useRef("ReceiptContent");
        this.inputRef = useRef("userInput");
        this.selectedProductFields = [];
        this.config_id =
            this.props.action?.params?.config_id ||
            this.props.action?.context?.pos_config_id ||
            this.props.action?.context?.active_id;
        this.dialog = useService("dialog");
        this.lastClickedTable = null;
        this.lastClickedColumnIndex = null;


        this.receipt_id = this.props.action?.params?.receipt_id || this.props.action?.context?.active_id;

        this.state = useState({
            fontStyle: "Arial",
            fields: [],
            logo: '',
            prev_logo: '',
            prev_receipt: '',
            receipt: '',
            model: '',
            showSection: false,
            showSection1: true,
            headerFields: [],
            draggedField: null,

            // NEW: QR Code settings
            qrSize: 120,
            qrPosition: "center",
            receiptQrSize: 120,
            receiptQrPosition: "center",

            popup: {
                visible: false,
                x: 0,
                y: 0,
                type: null,
                columnIndex: null,
                selectedField: "",
            },
        });

        onWillStart(async () => {
            await this.loadProductFields();
            await this.loadPosConfigId();
            await this.loadEnableQr();
            await this.loadQrSettings(); // NEW: Load QR settings
        });

        onMounted(async () => {
            await this.loadReceipt();
            await this.restoreSavedColumnsUniversal();
            await this.restoreSavedColumnsMaster();
            this.mediumEditor();
            this.preventPartialSelection();
            this.allowSpace();

            if (this.state.enableQr) {
                this.renderReceiptQr();
            }
        });
    }

    // NEW: Load QR settings from database
    async loadQrSettings() {
        if (!this.receipt_id) return;

        try {
            const [receipt] = await this.orm.read(
                "pos.receipt",
                [this.receipt_id],
                ["qr_size", "qr_position", "receipt_qr_size", "receipt_qr_position"]
            );

            if (receipt) {
                this.state.qrSize = receipt.qr_size || 120;
                this.state.qrPosition = receipt.qr_position || "center";
                this.state.receiptQrSize = receipt.receipt_qr_size || 120;
                this.state.receiptQrPosition = receipt.receipt_qr_position || "center";
            }
        } catch (error) {
            // Fields don't exist yet - use defaults
            console.log("QR settings fields not found, using defaults");
            this.state.qrSize = 120;
            this.state.qrPosition = "center";
            this.state.receiptQrSize = 120;
            this.state.receiptQrPosition = "center";
        }
    }

    // NEW: Handle URL QR size change
    onQrSizeChange(ev) {
        this.state.qrSize = parseInt(ev.target.value);
        this.updateCustomQr();
    }

    // NEW: Handle URL QR position change
    onQrPositionChange(ev) {
        this.state.qrPosition = ev.target.value;
        this.updateCustomQr();
    }

    // NEW: Handle Receipt QR size change
    onReceiptQrSizeChange(ev) {
        this.state.receiptQrSize = parseInt(ev.target.value);
        this.renderReceiptQr();
    }

    // NEW: Handle Receipt QR position change
    onReceiptQrPositionChange(ev) {
        this.state.receiptQrPosition = ev.target.value;
        this.renderReceiptQr();
    }

    // NEW: Update custom URL QR appearance
    updateCustomQr() {
        const editor = this.receiptContentRef.el;
        if (!editor) return;

        const targetArea = editor.querySelector(".qrArea");
        if (!targetArea) return;

        const qrPlaceholder = targetArea.querySelector(".custom-qr-placeholder");
        if (!qrPlaceholder) return;

        // Apply positioning
        const alignmentMap = {
            left: "flex-start",
            center: "center",
            right: "flex-end"
        };
        targetArea.style.display = "flex";
        targetArea.style.justifyContent = alignmentMap[this.state.qrPosition] || "center";

        // Apply size to QR
        const qrBox = qrPlaceholder.querySelector("div");
        if (qrBox) {
            const canvas = qrBox.querySelector("canvas");
            const img = qrBox.querySelector("img");

            if (canvas) {
                canvas.style.width = `${this.state.qrSize}px`;
                canvas.style.height = `${this.state.qrSize}px`;
            }
            if (img) {
                img.style.width = `${this.state.qrSize}px`;
                img.style.height = `${this.state.qrSize}px`;
            }
        }
    }

    applyFontStyle() {
        if (!this.receiptContentRef.el) return;

        const receiptDiv = this.receiptContentRef.el.querySelector('.pos-receipt');
        if (receiptDiv) {
            receiptDiv.style.fontFamily = this.state.fontStyle;
        }
    }

    async onProductFieldChange(ev) {
        const fieldName = ev.target.value;
        if (!fieldName) return;

        const mockData = await this.getMockProductData([fieldName]);
        this.addColumnAtIndexUniversal(fieldName, 0, mockData);
    }

    // UPDATED: Apply size and position settings
    renderReceiptQr() {
        if (!this.state.enableQr) return;

        const editor = this.receiptContentRef.el;
        if (!editor) return;

        const wrapper = editor.querySelector(".receipt-qr-wrapper");
        if (!wrapper) return;

        wrapper.querySelector(".receipt-qr-placeholder")?.remove();

        const templateImg = wrapper.querySelector(".receipt-qr-template img");
        if (!templateImg) return;

        const qrDiv = document.createElement("div");
        qrDiv.className = "receipt-qr-placeholder";

        // NEW: Apply positioning
        const alignmentMap = {
            left: "flex-start",
            center: "center",
            right: "flex-end"
        };

        qrDiv.style.display = "flex";
        qrDiv.style.justifyContent = alignmentMap[this.state.receiptQrPosition] || "center";
        qrDiv.style.marginTop = "12px";

        const img = templateImg.cloneNode(true);
        // NEW: Apply size
        img.style.width = `${this.state.receiptQrSize}px`;
        img.style.height = `${this.state.receiptQrSize}px`;
        img.style.margin = "0"; // Reset margin to allow flex positioning

        if (!this.props.data?.custom_qr_image) {
            const tempContainer = document.createElement('div');
            tempContainer.style.position = 'absolute';
            tempContainer.style.left = '-9999px';
            document.body.appendChild(tempContainer);

            new QRCode(tempContainer, {
                text: "Demo Receipt QR",
                width: this.state.receiptQrSize, // NEW: Use dynamic size
                height: this.state.receiptQrSize, // NEW: Use dynamic size
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });

            const qrCanvas = tempContainer.querySelector('canvas');
            const demoSrc = qrCanvas ? qrCanvas.toDataURL('image/png') : '';
            img.setAttribute('src', demoSrc);

            document.body.removeChild(tempContainer);
        }

        qrDiv.appendChild(img);
        wrapper.appendChild(qrDiv);
    }

    async restoreSavedColumns() {
        try {
            if (!this.receipt_id) {
                console.log("No receipt_id, skipping restore");
                return;
            }

            let retries = 0;
            const maxRetries = 10;
            while (!this.receiptContentRef?.el && retries < maxRetries) {
                console.log(`Waiting for receipt content... (${retries + 1}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 200));
                retries++;
            }

            if (!this.receiptContentRef?.el) {
                console.error("Receipt content not loaded after waiting");
                return;
            }

            const isDesign3 = this.isDesign3();

            if (isDesign3) {
                console.log("Design 3 detected - using row layout restore");
                return await this.restoreSavedColumnsDesign3();
            }

            console.log(" Table design detected - using table restore");

            const rec = await this.orm.read("pos.receipt", [this.receipt_id], ["selected_product_fields"]);
            const fields = JSON.parse(rec[0]?.selected_product_fields || "[]");

            if (!fields.length) {
                console.log("No fields to restore");
                return;
            }

            const mockData = await this.getMockProductData(fields);

            const table = this.receiptContentRef.el.querySelector(".receipt-table");

            if (!table) {
                console.error("No table found - cannot restore columns for table design");
                return;
            }

            const headerRow = table.querySelector("thead tr");

            if (!headerRow) {
                console.error("No header row found in table");
                return;
            }

            headerRow.querySelectorAll("th[data-field]").forEach(th => th.remove());
            table.querySelectorAll("td[data-field]").forEach(td => td.remove());

            fields.forEach(field => {
                this.addColumnAtIndex(field, 2, mockData);
            });

            console.log("Table columns restored successfully");

        } catch (error) {
            console.error("Error restoring columns:", error);
        }
    }

    async restoreSavedColumnsTable() {
        if (!this.receipt_id) return;

        let retries = 0;
        while (!this.receiptContentRef?.el?.querySelector(".receipt-table") && retries < 10) {
            await new Promise(resolve => setTimeout(resolve, 200));
            retries++;
        }

        const table = this.receiptContentRef.el?.querySelector(".receipt-table");
        if (!table) {
            console.error("Table not found");
            return;
        }

        const rec = await this.orm.read("pos.receipt", [this.receipt_id], ["selected_product_fields"]);
        const fields = JSON.parse(rec[0]?.selected_product_fields || "[]");

        if (!fields.length) return;

        const mockData = await this.getMockProductData(fields);

        const headerRow = table.querySelector("thead tr");

        headerRow.querySelectorAll("th[data-field]").forEach(th => th.remove());
        table.querySelectorAll("td[data-field]").forEach(td => td.remove());

        fields.forEach(field => {
            this.addColumnAtIndex(field, 2, mockData);
        });
    }

    async restoreSavedColumnsMaster() {
        try {
            await new Promise(resolve => setTimeout(resolve, 100));

            if (this.isDesign3()) {
                console.log("Restoring Design 3 columns...");
                await this.restoreSavedColumnsDesign3();
            } else {
                console.log("Restoring table columns...");
                await this.restoreSavedColumnsTable();
            }
        } catch (error) {
            console.error("Error in master restore:", error);
        }
    }

    async getMockProductData(fields = []) {
        if (!Array.isArray(fields) || fields.length === 0) {
            console.warn("getMockProductData: no fields provided, using fallback");

            return [{
                name: "Sample Product",
                qty: 1,
                price: 0,
            }];
        }

        try {
            const products = await this.orm.searchRead(
                "product.product",
                [],
                ["name", ...fields],
                { limit: 2 }
            );

            console.log("Mock product data:", products);
            return products;
        } catch (error) {
            console.error("Error fetching mock product data:", error);
            return [];
        }
    }

    enableColumnDropZones() {
        const table = this.receiptContentRef.el.querySelector(".receipt-table");

        if (this.isDesign3()) {
            this.enableColumnDropZonesDesign3();
            return;
        }

        if (!table) return;

        const headers = table.querySelectorAll(
            ".receipt-header-dropzone th"
        );

        headers.forEach((th, index) => {
            th.addEventListener("dragover", (ev) => {
                if (ev.dataTransfer.types.includes("application/x-pos-column")) {
                    ev.preventDefault();
                    th.classList.add("column-hover");
                }
            });

            th.addEventListener("dragleave", () => {
                th.classList.remove("column-hover");
            });

            th.addEventListener("drop", (ev) => {
                ev.preventDefault();
                th.classList.remove("column-hover");

                const fieldName = ev.dataTransfer.getData(
                    "application/x-pos-column"
                );

                if (!fieldName) return;

                this.addColumnAtIndex(fieldName, index);
            });
        });
    }

    enableColumnDropZonesDesign3() {
        const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");
        if (!dropzones) return;

        dropzones.forEach(zone => {
            zone.addEventListener("dragover", (ev) => {
                if (ev.dataTransfer.types.includes("application/x-pos-column")) {
                    ev.preventDefault();
                    zone.style.backgroundColor = "rgba(0, 123, 255, 0.1)";
                    zone.style.border = "2px dashed #007bff";
                }
            });

            zone.addEventListener("dragleave", () => {
                zone.style.backgroundColor = "";
                zone.style.border = "2px dashed #bbb";
            });

            zone.addEventListener("drop", (ev) => {
                zone.style.backgroundColor = "";
                zone.style.border = "2px dashed #bbb";
                this.onColumnDropDesign3(ev);
            });
        });
    }

    showPopup(type, x, y, colIndex) {
        this.closePopup();

        this.currentDialog = this.dialog.add(
            this.constructor.components.ColumnCellPopup,
            {
                type,
                colIndex,
                table: this.lastClickedTable,
                cell: this.lastClickedCell,
                x,
                y,
            }
        );
    }

    closePopup() {
        if (this.currentDialog) {
            this.currentDialog.close();
            this.currentDialog = null;
        }
    }

    async getPosConfig() {
        const [config] = await this.orm.searchRead(
            "pos.config",
            [],
            ["id", "selected_product_fields"],
            { limit: 1 }
        );
        return config;
    }

    async loadPosConfigId() {
        if (!this.receipt_id) {
            this.notification.add(
                "Receipt ID not found. Please open this from a receipt record.",
                { type: "danger" }
            );
            return;
        }

        const configs = await this.orm.searchRead(
            "pos.config",
            [["receipt_design_id", "=", this.receipt_id]],
            ["id"],
            { limit: 1 }
        );

        const config = configs[0];

        if (!config) {
            this.notification.add(
                "POS Config not found for this receipt. Please link a POS configuration.",
                { type: "warning" }
            );
            return;
        }

        this.config_id = config.id;
        console.log("POS CONFIG ID:", this.config_id);
    }

    async loadEnableQr() {
        try {
            const [receipt] = await this.orm.read(
                "pos.receipt",
                [this.receipt_id],
                ["enable_qr", "enable_qr_section"]
            );

            this.state.enableQr = !!receipt?.enable_qr;
            this.state.showSection = !!receipt?.enable_qr_section;

            console.log("Loaded enable_qr:", this.state.enableQr);
            console.log("Loaded enable_qr_section:", this.state.showSection);
        } catch (error) {
            console.warn("Could not load QR enable fields:", error);
            this.state.enableQr = false;
            this.state.showSection = false;
        }
    }

    async mediumEditor() {
        this.editor = new MediumEditor(this.receiptContentRef.el, {
            toolbar: {
                buttons: ['bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', 'h1', 'h3', 'quote', 'anchor'],
            },
            placeholder: false,
            targetBlank: true,
            disableExtraSpaces: true,
        });
    }

    async allowSpace() {
        if (!this.receiptContentRef.el) return;
        this.receiptContentRef.el.addEventListener("keydown", (ev) => {
            if (ev.key === " " || ev.keyCode === 32) {
                const sel = window.getSelection();
                if (!sel.rangeCount) return;
                const range = sel.getRangeAt(0);
                if (
                    range.startContainer.nodeType === Node.TEXT_NODE &&
                    range.startOffset === range.startContainer.length
                ) {
                    ev.preventDefault();
                    document.execCommand("insertHTML", false, "&nbsp;");
                }
            }
        });
    }

    preventPartialSelection() {
        document.addEventListener("selectionchange", () => {
            const sel = window.getSelection();
            if (!sel.rangeCount) return;
            const range = sel.getRangeAt(0);
            const startEl = range.startContainer.parentElement;
            const endEl = range.endContainer.parentElement;
            const placeholder = startEl.closest(".placeholder-span") || endEl.closest(".placeholder-span");
            if (placeholder && sel.toString() !== placeholder.textContent) {
                const newRange = document.createRange();
                newRange.selectNodeContents(placeholder);
                sel.removeAllRanges();
                sel.addRange(newRange);
            }
        });
    }

    async loadReceipt(reset = false) {
        const [receipt] = await this.orm.searchRead(
            "pos.receipt",
            [["id", "=", this.receipt_id]],
            ["name", "design_receipt", "design_receipt_font_style", "logo"]
        );
        if (!receipt) return;
        this.state.fontStyle = receipt.design_receipt_font_style || "Arial";
        this.state.logo = receipt.logo
        if (!reset && this.receiptContentRef.el?.innerHTML) {
            this.state.receipt = this.receiptContentRef.el.innerHTML;
        } else {
            this.state.receipt = receipt.design_receipt;
        }
        let html = this.state.receipt

        if (typeof html !== 'string') {
            if (html === null || html === undefined || html === false) {
                html = "";
            } else {
                this.notification.add(`Invalid receipt design format (${typeof html}). Expected XML string.`, { type: 'warning' });
                html = String(html);
            }
        }

        let logo;
        if (reset === false || !this.state.prev_logo) {
            logo = this.state.logo;
        } else {
            logo = this.state.prev_logo;
        }
        this.state.logo = logo;
        html = html.replace(/<img[^>]*class="receipt-logo"[^>]*>/gi, "");
        html = html.replace(/<t t-else="">\s*<\/t>/gi, "");
        html = html.replace(/<t>\s*<\/t>/gi, "");
        if (logo) {
            html = html.replace(
                /<t t-if="env.services.pos.config.logo">[\s\S]*?<\/t>/,
                `<t t-if="env.services.pos.config.logo">
                    <img t-att-src="'data:image/png;base64,' + env.services.pos.config.logo"
                         class="pos-receipt-logo"/>
                </t>
                <t t-else="">
                <img src="data:image/png;base64,${logo}"
                     class="receipt-logo" style="max-width:150px;height:auto;"/>
                </t>`
            );
        }
        this.receiptContentRef.el.innerHTML = html;
        this.applyFontStyle();
        this.enableColumnDropZones();
    }

    triggerImageUpload() {
        document.getElementById("imageUpload")?.click();
    }

    async insertImage(ev) {
        const file = ev.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async () => {
            const base64 = reader.result.split(",")[1];
            this.state.receipt = this.receiptContentRef.el.innerHTML;
            this.state.prev_logo = this.state.logo;
            this.state.prev_receipt = this.state.receipt;
            await this.orm.write("pos.receipt", [this.receipt_id], { logo: base64 });
            this.state.logo = base64;
            await this.loadReceipt();
            this.notification.add("Receipt Logo Updated!", {
                type: "success",
            });
        };
        reader.readAsDataURL(file);
    }

    async saveEditedReceipt() {
        const clone = this.receiptContentRef.el.cloneNode(true);

        if (this.isDesign3()) {
            const dropzones = clone.querySelectorAll(".receipt-header-dropzone");
            dropzones.forEach(dz => {
                dz.innerHTML = '<span class="customizer-only-text"></span>';
            });
        }

        this.state.receipt = clone.innerHTML;
        this.state.receipt = this.state.receipt.replace(/Display Name/gi, "");
        this.state.receipt = this.state.receipt.replace(/display_name/gi, "");

        const dataToSave = {
            design_receipt: this.state.receipt,
            design_receipt_font_style: this.state.fontStyle,
            logo: this.state.logo,
            enable_qr: !!this.state.enableQr,
            enable_qr_section: !!this.state.showSection,
        };

        try {
            dataToSave.qr_size = this.state.qrSize;
            dataToSave.qr_position = this.state.qrPosition;
            dataToSave.receipt_qr_size = this.state.receiptQrSize;
            dataToSave.receipt_qr_position = this.state.receiptQrPosition;

            await this.orm.write("pos.receipt", [this.receipt_id], dataToSave);
        } catch (error) {
            console.log("QR settings fields not available, saving without them");
            delete dataToSave.qr_size;
            delete dataToSave.qr_position;
            delete dataToSave.receipt_qr_size;
            delete dataToSave.receipt_qr_position;

            await this.orm.write("pos.receipt", [this.receipt_id], dataToSave);
        }

        console.log("FONTSTYLE", this.state.fontStyle)

        this.notification.add("Receipt Successfully Updated!", {
            type: "success",
        });

        setTimeout(() => window.location.reload(), 800);
    }

    async resetEditedReceipt() {
        if (this.state.prev_receipt) {
            this.state.receipt = this.state.prev_receipt;
            this.receiptContentRef.el.innerHTML = this.state.receipt;
        }
        await this.loadReceipt(true);
        this.notification.add(" Receipt Reset Completed!", {
            type: "success",
        });
    }

    onFontChange(ev) {
        this.state.fontStyle = ev.target.value;
        this.applyFontStyle();
    }

    async onModelChange(ev) {
        const model = ev.target.value;
        this.state.model = model
        if (!model) return (this.state.fields = []);
        const fields = await this.orm.call(model, "fields_get", [], {});
        this.state.fieldsInfo = fields;
        const prefix = model === "pos.order" ? "order" :
            model === "res.partner" ? "partner" : model;
        this.state.fields = Object.keys(fields).filter(key => !/(_ids?$|\d+$)/.test(key)).map((key) => ({
            technical: `${prefix}.${key}`,
            label: odoo.debug
                ? `${fields[key].string || key} (${prefix}.${key})`
                : fields[key].string || key,
        }));
    }

    onDragStart(ev) {
        console.log("DARG!!!!")
        const field = `[[${ev.target.dataset.field}]]`;
        ev.dataTransfer.setData("text/plain", field);
        ev.dataTransfer.effectAllowed = "copy";
        const ghost = document.createElement("div");
        ghost.textContent = field;
        ghost.style.padding = "6px 12px";
        ghost.style.fontSize = "12px";
        ghost.style.fontWeight = "400";
        ghost.style.background = "#000000";
        ghost.style.color = "black";
        ghost.style.borderRadius = "20px";
        ghost.style.boxShadow = "0 2px 6px rgba(0,0,0,0.15)";
        ghost.style.pointerEvents = "none";
        ghost.style.position = "absolute";
        ghost.style.top = "-9999px";
        ghost.style.left = "-9999px";
        document.body.appendChild(ghost);
        ev.dataTransfer.setDragImage(ghost, 0, 0);
        setTimeout(() => ghost.remove(), 0);
        this.receiptContentRef.el.classList.add("dragging");
        this.receiptContentRef.el.classList.add("drop-highlight");
    }

    onDragEnd() {
        this.receiptContentRef.el.classList.remove("dragging");
        console.log("DAGGEDEND!!!!1")
        this.receiptContentRef.el.classList.remove("drop-highlight");
    }

    onDrop(ev) {
        ev.preventDefault();
        console.log("DROP!@#$")

        if (ev.dataTransfer.types.includes("application/x-pos-column")) {
            return;
        }

        const noDropZone = ev.target.closest(".no-drop-zone");
        if (noDropZone) {
            console.warn("Drop blocked in protected area (no-drop-zone)");
            this.notification.add("Cannot drop fields in this area. Use designated drop zones only.", {
                type: "warning"
            });
            return;
        }

        if (ev.target.closest(".receipt-header")) {
            console.warn("Drop blocked in receipt header");
            return;
        }

        const editor = this.receiptContentRef.el;
        console.log("EDITOR", editor)

        const fieldText = ev.dataTransfer.getData("text/plain");
        if (!fieldText) return;

        const span = document.createElement("span");
        span.textContent = fieldText;
        span.classList.add("placeholder-span");

        const placeholder = ev.target.closest(".placeholder-span");
        if (placeholder) {
            placeholder.insertAdjacentElement("afterend", span);
            return;
        }

        let range = null;
        if (document.caretRangeFromPoint) {
            range = document.caretRangeFromPoint(ev.clientX, ev.clientY);
        } else if (document.caretPositionFromPoint) {
            const pos = document.caretPositionFromPoint(ev.clientX, ev.clientY);
            if (pos?.offsetNode) {
                range = document.createRange();
                range.setStart(pos.offsetNode, pos.offset);
                range.collapse(true);
            }
        }

        if (range) {
            range.insertNode(span);
        } else {
            const targetArea = editor.querySelector(".drop-area");
            if (targetArea) {
                targetArea.appendChild(span);
            }
        }

        this.receiptContentRef.el.classList.remove("dragging");
        this.receiptContentRef.el.classList.remove("drop-highlight");

        span.classList.add("added");
        setTimeout(() => span.classList.remove("added"), 400);
    }

    onColumnDragStart(ev) {
        ev.stopPropagation();
        ev.dataTransfer.setData(
            "application/x-pos-column",
            ev.target.dataset.field
        );
        ev.dataTransfer.effectAllowed = "copy";
        this.receiptContentRef.el.classList.add("column-dragging");
    }

    addColumnAtIndex(fieldName, index, mockData = null) {
        const table = this.receiptContentRef.el.querySelector(".receipt-table");
        if (!table) return;

        const headerRow = table.querySelector("thead tr");
        const bodyRows = table.querySelectorAll("tbody tr");

        if (headerRow.querySelector(`[data-field="${fieldName}"]`)) {
            this.notification.add("Column already added", { type: "warning" });
            return;
        }

        const existingDynamicColumns = headerRow.querySelectorAll("th[data-field]");
        if (existingDynamicColumns.length >= 1) {
            this.notification.add(
                "Only one additional column is allowed. Please remove the existing column first.",
                { type: "warning" }
            );
            return;
        }

        const staticHeaders = headerRow.querySelectorAll("th:not([data-field])");
        if (staticHeaders.length >= 3) {
            staticHeaders[0].style.width = "35%";
            staticHeaders[1].style.width = "12%";
            staticHeaders[2].style.width = "18%";
        }

        const th = document.createElement("th");
        th.dataset.field = fieldName;

        const fieldObj = this.state.productFields?.find(f => f.name === fieldName);
        th.textContent = fieldObj?.label || fieldName
            .replaceAll("_", " ")
            .toLowerCase()
            .replace(/\b\w/g, c => c.toUpperCase());

        th.style.textAlign = "center";
        th.style.width = "35%";
        th.style.padding = "12px";
        th.style.whiteSpace = "nowrap";
        th.style.fontFamily = "inherit";
        th.style.overflow = "visible";
        th.style.fontSize = "12px";

        headerRow.appendChild(th);

        bodyRows.forEach((row, rowIndex) => {
            const staticCells = row.querySelectorAll("td:not([data-field])");
            if (staticCells.length >= 3) {
                staticCells[0].style.width = "35%";
                staticCells[1].style.width = "12%";
                staticCells[2].style.width = "18%";
            }

            if (row.querySelector(`td[data-field="${fieldName}"]`)) return;

            const td = document.createElement("td");
            td.dataset.field = fieldName;
            td.style.padding = "4px";
            td.style.textAlign = "center";
            td.style.width = "35%";
            td.style.whiteSpace = "nowrap";
            td.style.verticalAlign = "top";
            td.style.fontFamily = "inherit";
            td.style.overflow = "visible";

            let value = "";

            if (mockData && Array.isArray(mockData) && mockData[rowIndex]) {
                value = mockData[rowIndex][fieldName] || "";

                if (typeof value === 'number') {
                    value = value.toFixed(2);
                } else if (Array.isArray(value)) {
                    value = value[1] || value[0] || "";
                } else if (typeof value === 'boolean') {
                    value = value ? 'Yes' : 'No';
                }
            }
            else {
                const lines = this.props.orderlines || this.props.lines || [];
                const line = lines[rowIndex];

                if (line && line._dynamicValues && fieldName in line._dynamicValues) {
                    value = line._dynamicValues[fieldName];
                }
            }

            td.textContent = " " || " ";
            row.appendChild(td);
        });

        this.saveSelectedColumns();
    }

    saveSelectedColumns() {
        const table = this.receiptContentRef.el.querySelector(".receipt-table");
        if (!table) return;

        const headerRow = table.querySelector("thead tr");
        if (!headerRow) return;

        const fields = [];

        [...headerRow.children].forEach(th => {
            const field = th.dataset.field;
            if (field) {
                fields.push(field);
            }
        });

        this.selectedProductFields = fields;

        if (this.receipt_id) {
            this.orm.write("pos.receipt", [this.receipt_id], {
                selected_product_fields: JSON.stringify(fields),
            });
        }

        console.log("Saved receipt columns:", fields);
    }

    showInput() {
        this.state.showSection = true;
        this.state.showSection1 = false;
    }

    submitValue() {
        if (!this.state.showSection) return;

        const value = this.inputRef.el?.value?.trim();
        if (!value) {
            this.notification.add("Please enter a value!", { type: "warning" });
            return;
        }

        const editor = this.receiptContentRef.el;
        const targetArea = editor?.querySelector(".qrArea");
        if (!targetArea) return;

        targetArea.querySelector(".custom-qr-placeholder")?.remove();

        const qrDiv = document.createElement("div");
        qrDiv.className = "custom-qr-placeholder";

        const qrBox = document.createElement("div");
        qrDiv.appendChild(qrBox);
        targetArea.appendChild(qrDiv);

        new QRCode(qrBox, {
            text: value,
            width: this.state.qrSize, // NEW: Use dynamic size
            height: this.state.qrSize, // NEW: Use dynamic size
        });

        // NEW: Apply positioning
        this.updateCustomQr();
    }

    onToggleQr(ev) {
        const checked = ev.target.checked;
        const editor = this.receiptContentRef.el;
        const target = editor?.querySelector(".qrArea");

        if (!checked) {
            target?.querySelector(".custom-qr-placeholder")?.remove();
            return;
        }

        this.submitValue();
    }

    onToggleReceiptQr(ev) {
        this.state.enableQr = ev.target.checked;

        const editor = this.receiptContentRef.el;
        const wrapper = editor?.querySelector(".receipt-qr-wrapper");
        if (!wrapper) return;

        wrapper.querySelector(".receipt-qr-placeholder")?.remove();

        if (this.state.enableQr) {
            this.renderReceiptQr();
        }
    }

    async onReceiptClick(ev) {
        if (this.receiptContentRef.el.classList.contains("column-dragging")) {
            return;
        }

        // NEW: Check for logo click
        const logo = ev.target.closest(".pos-receipt-logo") || ev.target.closest(".receipt-logo");
        if (logo) {
            this.dialog.add(ConfirmationDialog, {
                title: "Remove Logo",
                body: "Are you sure you want to remove the logo from the receipt?",
                confirm: () => this.removeLogo(),
                cancel: () => { },
            });
            return;
        }

        if (this.isDesign3()) {
            const fieldEl = ev.target.closest(".design3-row-layout [data-field]");
            if (fieldEl) {
                const fieldName = fieldEl.dataset.field;
                this.dialog.add(ConfirmationDialog, {
                    title: "Remove Field",
                    body: `Remove field "${fieldName}"?`,
                    confirm: () => this.removeColumnDesign3(fieldName),
                    cancel: () => { },
                });
            }
            return;
        }

        const table = ev.target.closest("table");
        if (!table) return;

        const th = ev.target.closest("th");
        if (!th) return;

        const colIndex = Array.from(th.parentNode.children).indexOf(th);
        const fieldName = th?.dataset?.field;

        if (!fieldName || colIndex < 3) {
            this.notification.add("Cannot remove this column.", { type: "warning" });
            return;
        }

        this.lastClickedTable = table;
        this.lastClickedColumnIndex = colIndex;

        this.dialog.add(ConfirmationDialog, {
            title: "Remove Column",
            body: `Remove column "${fieldName}"?`,
            confirm: () => this.onRemoveColumnClick(colIndex),
            cancel: () => { },
        });
    }

    async removeLogo() {
        try {
            this.state.logo = false;
            this.state.prev_logo = false;

            // Remove from DOM immediately for feedback
            const logoEl = this.receiptContentRef.el.querySelector(".pos-receipt-logo") ||
                this.receiptContentRef.el.querySelector(".receipt-logo");
            if (logoEl) {
                logoEl.remove();
            }

            // Update backend
            await this.orm.write("pos.receipt", [this.receipt_id], { logo: false });

            // Reload to ensure state consistency
            await this.loadReceipt();

            this.notification.add("Logo removed successfully", { type: "success" });
        } catch (error) {
            console.error("Error removing logo:", error);
            this.notification.add("Failed to remove logo", { type: "danger" });
        }
    }

    async loadProductFields() {
        const fields = await this.orm.call("product.product", "fields_get", [], {});

        this.state.productFields = Object.keys(fields)
            .filter(k => !/(_ids?$|\d+$)/.test(k))
            .map(k => ({
                name: k,
                label: fields[k].string || k,
            }));
    }

    onPopupFieldChange(ev) {
        this.state.popup.selectedField = ev.target.value || "";
    }

    async onAddColumnClick() {
        const fieldName = this.state.popup.selectedField;

        if (!fieldName) {
            this.notification.add("Please select a field.", { type: "warning" });
            return;
        }
        if (!this.lastClickedTable) {
            this.notification.add("Click a table first.", { type: "danger" });
            return;
        }
        if (!this.receipt_id) {
            this.notification.add("Receipt ID not found", { type: "danger" });
            return;
        }

        const table = this.lastClickedTable;
        let headerRow = table.querySelector("thead tr") || table.querySelector("tr");
        if (!headerRow) return;

        let bodyRows = table.querySelectorAll("tbody tr");
        if (!bodyRows.length) {
            bodyRows = Array.from(table.querySelectorAll("tr")).slice(1);
        }

        const insertIndex = headerRow.children.length;

        const fieldObj = this.state.productFields.find(f => f.name === fieldName);
        const label = fieldObj?.label || fieldName;

        if (!this.selectedProductFields.includes(fieldName)) {
            this.selectedProductFields.push(fieldName);
        }

        const th = document.createElement("th");
        th.textContent = label;
        th.setAttribute("data-field", fieldName);
        headerRow.appendChild(th);

        bodyRows.forEach((row) => {
            const td = document.createElement("td");
            td.setAttribute("data-field", fieldName);
            td.style.padding = "4px";

            const span = document.createElement("span");
            td.appendChild(span);
            row.appendChild(td);
        });

        await this.orm.write("pos.receipt", [this.receipt_id], {
            selected_product_fields: JSON.stringify(this.selectedProductFields),
        });


        this.hidePopup();
    }

    saveDesignToConfig() {
        const receiptDiv = document.querySelector('.pos-receipt');
        if (!receiptDiv) {
            console.error("Receipt div not found");
            return;
        }

        let updatedDesign = receiptDiv.outerHTML;
        updatedDesign = updatedDesign
            .replace(/\sdata-[^=]*="[^"]*"/g, '')
            .replace(/\sclass="[^"]*"/g, (match) => {
                if (match.includes('pos-receipt') || match.includes('placeholder-span')) {
                    return match;
                }
                return '';
            });

        const selectedFields = this.extractFieldsFromDesign(updatedDesign);

        this.orm
            .call('pos.receipt', 'write', [[this.receipt_id], {
                design_receipt: updatedDesign,
                selected_product_fields: JSON.stringify(selectedFields),
            }])
            .then(() => {
                this.notification.add("Design saved successfully!", { type: "success" });
            })
            .catch((error) => {
                console.error("Save error:", error);
                this.notification.add("Failed to save", { type: "danger" });
            });
    }

    extractFieldsFromDesign(html) {
        const fields = new Set();
        const regex = /\[\[\s*orderline\.([\w_]+)\s*\]\]/g;
        let match;

        while ((match = regex.exec(html)) !== null) {
            fields.add(match[1]);
        }

        return Array.from(fields);
    }

    async onRemoveColumnClick(colIndex = null) {
        if (!this.lastClickedTable) {
            this.notification.add("No table selected.", { type: "danger" });
            return;
        }

        const table = this.lastClickedTable;
        const theadRow = table.querySelector("thead tr");
        const bodyRows = table.querySelectorAll("tbody tr");

        const STATIC_COL_COUNT = 3;
        const columnIndex = colIndex ?? this.lastClickedColumnIndex;

        if (columnIndex == null || columnIndex < STATIC_COL_COUNT) {
            this.notification.add("You cannot remove default columns.", { type: "warning" });
            return;
        }

        const th = theadRow.children[columnIndex];
        const fieldName = th?.dataset?.field;
        if (!fieldName) return;

        const [receipt] = await this.orm.searchRead(
            "pos.receipt",
            [["id", "=", this.receipt_id]],
            ["selected_product_fields"],
            { limit: 1 }
        );

        let fields = JSON.parse(receipt?.selected_product_fields || "[]");
        fields = fields.filter(f => f !== fieldName);

        await this.orm.write("pos.receipt", [this.receipt_id], {
            selected_product_fields: JSON.stringify(fields),
        });

        th.remove();

        bodyRows.forEach(row => {
            const cell = row.querySelector(`td[data-field="${fieldName}"]`);
            if (cell) cell.remove();
        });

        this.notification.add(`Column "${fieldName}" removed`, { type: "success" });

        this.lastClickedTable = null;
        this.lastClickedColumnIndex = null;
    }

    onInsertFieldClick() {
        const fieldTechnical = this.state.popup.selectedField;
        if (!fieldTechnical) {
            this.notification.add("Please select a field to insert.", {
                type: "warning",
            });
            return;
        }
        if (!this.lastClickedCell) {
            this.notification.add("No cell selected to insert into.", {
                type: "danger",
            });
            this.hidePopup();
            return;
        }

        const cell = this.lastClickedCell;

        if (!cell.textContent.trim()) {
            cell.innerHTML = "";
        }

        const span = document.createElement("span");
        span.classList.add("placeholder-span");
        span.textContent = `[[${fieldTechnical}]]`;

        if (cell.lastChild) {
            cell.appendChild(document.createTextNode(" "));
        }
        cell.appendChild(span);

        if (this._animateSpan) {
            this._animateSpan(span);
        }

        this.hidePopup();
    }

    isDesign3() {
        const el = this.receiptContentRef?.el;
        if (!el) {
            return false;
        }

        return !!el.querySelector(".design3-row-layout");
    }

    addColumnAtIndexDesign3(fieldName, index, mockData = null) {
        try {
            if (!this.receiptContentRef?.el) {
                console.error("Receipt content ref not available");
                return;
            }

            const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");

            if (!dropzones || dropzones.length === 0) {
                console.warn("No dropzones found in Design 3");
                this.notification?.add?.("This receipt design doesn't support dynamic fields", {
                    type: "warning"
                });
                return;
            }

            const existing = this.receiptContentRef.el.querySelector(`.receipt-header-dropzone [data-field="${fieldName}"]`);
            if (existing) {
                this.notification?.add?.("Field already added", { type: "warning" });
                return;
            }

            const existingFieldCount = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone [data-field]").length;

            if (existingFieldCount >= 3) {
                this.notification?.add?.(
                    "Maximum 3 additional fields allowed. Remove existing fields first.",
                    { type: "warning" }
                );
                return;
            }

            const fieldObj = this.state.productFields?.find(f => f.name === fieldName);
            const fieldLabel = fieldObj?.label || fieldName
                .replaceAll("_", " ")
                .toLowerCase()
                .replace(/\b\w/g, c => c.toUpperCase());

            dropzones.forEach((dropzone, rowIndex) => {
                if (dropzone.querySelector(`[data-field="${fieldName}"]`)) {
                    return;
                }
                const fieldDiv = document.createElement("div");
                fieldDiv.dataset.field = fieldName;
                fieldDiv.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                font-size: 13px;
                margin-bottom: 6px;
                padding: 4px 0;
                cursor: pointer;
            `;
                fieldDiv.title = "Click to remove";

                const labelSpan = document.createElement("span");
                labelSpan.style.cssText = "opacity: 0.7; font-weight: 500;";
                labelSpan.textContent = fieldLabel;

                const valueSpan = document.createElement("span");
                valueSpan.style.cssText = "font-weight: 600; text-align: right; word-break: break-word; max-width: 60%;";
                valueSpan.classList.add("placeholder-span");

                let value = "";

                if (mockData && Array.isArray(mockData) && mockData[rowIndex]) {
                    value = mockData[rowIndex][fieldName] || "";

                    if (typeof value === 'number') {
                        value = value.toFixed(2);
                    } else if (Array.isArray(value)) {
                        value = value[1] || value[0] || "";
                    } else if (typeof value === 'boolean') {
                        value = value ? 'Yes' : 'No';
                    }

                    valueSpan.textContent = " " || " ";
                } else {
                    const lines = this.props?.orderlines || this.props?.lines || [];
                    const line = lines[rowIndex];

                    if (line && line._dynamicValues && fieldName in line._dynamicValues) {
                        value = line._dynamicValues[fieldName];
                        valueSpan.textContent = value;
                    } else {
                        valueSpan.textContent = `[[ orderline.${fieldName} ]]`;
                    }
                }

                fieldDiv.appendChild(labelSpan);
                fieldDiv.appendChild(valueSpan);
                dropzone.appendChild(fieldDiv);
            });

            this.saveSelectedColumnsDesign3();

            this.notification?.add?.(`Field "${fieldLabel}" added successfully`, {
                type: "success"
            });
        } catch (error) {
            console.error("Error adding Design 3 column:", error);
            this.notification?.add?.("Failed to add field", { type: "danger" });
        }
    }

    saveSelectedColumnsDesign3() {
        try {
            if (!this.receiptContentRef?.el) {
                console.warn("Receipt content not available for saving");
                return;
            }

            const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");
            if (!dropzones || dropzones.length === 0) {
                console.warn("No dropzones found for saving");
                return;
            }

            const fields = [];

            dropzones.forEach(dropzone => {
                const fieldElements = dropzone.querySelectorAll("[data-field]");
                fieldElements.forEach(elem => {
                    const field = elem.dataset.field;
                    if (field && !fields.includes(field)) {
                        fields.push(field);
                    }
                });
            });

            this.selectedProductFields = fields;

            if (this.receipt_id && this.orm) {
                this.orm.write("pos.receipt", [this.receipt_id], {
                    selected_product_fields: JSON.stringify(fields),
                });
            }

        } catch (error) {
            console.error("Error saving Design 3 columns:", error);
        }
    }

    async restoreSavedColumnsDesign3() {
        try {
            console.log("Starting Design 3 column restoration...");

            if (!this.receipt_id) {
                console.warn("No receipt_id for restoring");
                return;
            }

            let retries = 0;
            const maxRetries = 10;
            while ((!this.receiptContentRef?.el || !this.receiptContentRef.el.querySelector(".receipt-header-dropzone")) && retries < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, 200));
                retries++;
            }

            if (!this.receiptContentRef?.el) {
                console.error("Receipt content still not available after waiting");
                return;
            }

            const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");
            if (!dropzones || dropzones.length === 0) {
                console.error("No dropzones found after waiting");
                return;
            }


            const receipt = await this.orm.read("pos.receipt", [this.receipt_id], [
                "selected_product_fields",
            ]);

            if (!receipt || !receipt[0]?.selected_product_fields) {
                return;
            }

            let fields = [];
            try {
                fields = JSON.parse(receipt[0].selected_product_fields);
            } catch (e) {
                console.error("Failed to parse saved fields:", e);
                return;
            }

            if (!Array.isArray(fields) || fields.length === 0) {

                return;
            }


            const mockData = await this.getMockProductData(fields);

            for (const field of fields) {
                this.addColumnAtIndexDesign3(field, 0, mockData);
            }

        } catch (error) {
            console.error("Error restoring Design 3 columns:", error);
        }
    }

    removeColumnDesign3(fieldName) {
        try {
            if (!this.receiptContentRef?.el) {
                console.error("Receipt content not available");
                return;
            }

            const fieldsToRemove = this.receiptContentRef.el.querySelectorAll(
                `.receipt-header-dropzone [data-field="${fieldName}"]`
            );

            if (fieldsToRemove.length === 0) {
                this.notification?.add?.("Field not found", { type: "warning" });
                return;
            }

            fieldsToRemove.forEach(elem => elem.remove());

            this.saveSelectedColumnsDesign3();

            const fieldObj = this.state.productFields?.find(f => f.name === fieldName);
            const fieldLabel = fieldObj?.label || fieldName;

            this.notification?.add?.(`Field "${fieldLabel}" removed`, { type: "success" });
        } catch (error) {
            console.error("Error removing Design 3 column:", error);
            this.notification?.add?.("Failed to remove field", { type: "danger" });
        }
    }

    onColumnDragStartDesign3(ev) {
        try {
            ev.stopPropagation();
            const dragEl = ev.target.closest("[data-field]");
            const fieldName = dragEl?.dataset.field;
            console.log("FIELDNAME", fieldName)

            if (!fieldName) {
                console.warn("No field name found on drag element");
                return;
            }

            ev.dataTransfer.setData("application/x-pos-column", fieldName);
            ev.dataTransfer.effectAllowed = "copy";

            if (!this.receiptContentRef?.el) return;

            this.receiptContentRef.el.classList.add("column-dragging");

            const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");
            dropzones.forEach(zone => {
                zone.style.border = "2px dashed #007bff";
                zone.style.minHeight = "40px";
                zone.style.backgroundColor = "rgba(0, 123, 255, 0.05)";
                zone.style.transition = "all 0.3s ease";
            });
        } catch (error) {
            console.error("Error on drag start:", error);
        }
    }

    onColumnDragEndDesign3(ev) {
        try {
            if (!this.receiptContentRef?.el) return;

            this.receiptContentRef.el.classList.remove("column-dragging");

            const dropzones = this.receiptContentRef.el.querySelectorAll(".receipt-header-dropzone");

            dropzones.forEach(zone => {
                zone.style.border = "";
                zone.style.minHeight = "";
                zone.style.backgroundColor = "";
                zone.style.transition = "";
            });

        } catch (error) {
            console.error("Error on drag end:", error);
        }
    }

    async onColumnDropDesign3(ev) {
        try {
            ev.preventDefault();
            ev.stopPropagation();

            const fieldName = ev.dataTransfer.getData("application/x-pos-column");
            if (!fieldName) return;

            const dropzone = ev.target.closest(".receipt-header-dropzone");
            if (!dropzone) return;

            const rowIndex = parseInt(dropzone.dataset.rowIndex, 10);

            let mockData = null;
            try {
                mockData = await this.getMockProductData([fieldName]);
            } catch { }

            this.addColumnAtIndexDesign3(fieldName, rowIndex, mockData);

            this.onColumnDragEndDesign3(ev);

        } catch (error) {
            console.error("Error on column drop:", error);
        }
    }

    async restoreSavedColumnsUniversal() {
        try {
            console.log("Detecting design type...");

            await new Promise(resolve => setTimeout(resolve, 100));

            if (this.isDesign3()) {
                console.log("Design 3 detected");
                return await this.restoreSavedColumnsDesign3();
            } else {
                console.log("Table design detected");
                if (typeof this.restoreSavedColumns === 'function') {
                    return await this.restoreSavedColumns();
                } else {
                    console.warn("restoreSavedColumns function not found");
                }
            }
        } catch (error) {
            console.error("Error in universal restore:", error);
        }
    }

    addColumnAtIndexUniversal(fieldName, index = 0, mockData = null) {
        try {
            if (!fieldName) {
                console.warn("addColumnAtIndexUniversal: fieldName missing");
                return;
            }

            if (!this.receiptContentRef?.el) {
                console.warn("Receipt DOM not ready yet");
                return;
            }

            if (this.isDesign3()) {
                console.log(" Adding column  Design 3 (row layout)");
                return this.addColumnAtIndexDesign3(fieldName, index, mockData);
            }

            if (typeof this.addColumnAtIndex === "function") {
                console.log(" Adding column  Table design (Design 1 / 2)");
                return this.addColumnAtIndex(fieldName, index, mockData);
            }

            console.warn("addColumnAtIndex not implemented for table designs");

        } catch (error) {
            console.error("Error in addColumnAtIndexUniversal:", error);
        }
    }

    saveSelectedColumnsUniversal() {
        try {
            if (!this.receiptContentRef?.el) {
                console.warn("Receipt DOM not ready for saving");
                return;
            }

            if (this.isDesign3()) {
                console.log("Saving columns → Design 3");
                return this.saveSelectedColumnsDesign3();
            }

            if (typeof this.saveSelectedColumns === "function") {
                console.log("Saving columns  Table design (Design 1 / 2)");
                return this.saveSelectedColumns();
            }

            console.warn("saveSelectedColumns not implemented for table designs");

        } catch (error) {
            console.error(" Error in saveSelectedColumnsUniversal:", error);
        }
    }

}

registry.category("actions").add("pos_receipt_layout_client_action", PosReceiptLayoutClientAction);