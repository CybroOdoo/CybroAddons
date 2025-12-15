/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class PosReceiptLayoutClientAction extends Component {
    static template = "custom_receipt_for_pos.client_layout_customisation_template";
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.receiptContentRef = useRef("ReceiptContent");
        this.receipt_id = this.props.action.context.active_id;
        console.log(this.receipt_id )
        this.state = useState({
            fontStyle: "Arial",
            fields: [],
            logo: '',
            prev_logo: '',
            prev_receipt: '',
            receipt: '',
            model: '',
        });

        onMounted(async () => {
            await this.loadReceipt();
            this.mediumEditor();
            this.preventPartialSelection();
            this.allowSpace();
        });
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

    async allowSpace(){
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

    async loadReceipt(reset=false) {
        const [receipt] = await this.orm.searchRead(
            "pos.receipt",
            [["id", "=", this.receipt_id]],
            ["name", "design_receipt", "design_receipt_font_style", "logo"]
        );

        console.log("Loaded receipt:", receipt);
        console.log(receipt.name)
        if (!receipt) return;
        this.state.fontStyle = receipt.design_receipt_font_style || "Arial";
        this.state.logo = receipt.logo
        if (!reset && this.receiptContentRef.el?.innerHTML) {
            this.state.receipt = this.receiptContentRef.el.innerHTML;
        }
        else {
            this.state.receipt = receipt.design_receipt;
        }
        let html = this.state.receipt
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
            this.notification.add("✅ Receipt Logo Updated!", {
                type: "success",
            });
        };
        reader.readAsDataURL(file);
    }

    async saveEditedReceipt() {
        this.state.receipt = this.receiptContentRef.el.innerHTML
        this.state.prev_logo = this.state.logo
        this.state.prev_receipt = this.state.receipt
        const html = this.state.receipt
        await this.orm.write("pos.receipt", [this.receipt_id], {
            design_receipt: html,
            design_receipt_font_style: this.state.fontStyle,
            logo: this.state.logo,
        });
        this.notification.add("✅ Receipt Successfully Updated!", {
                type: "success",
            });
    }

    async resetEditedReceipt(){
        if (this.state.prev_receipt) {
            this.state.receipt = this.state.prev_receipt;
            this.receiptContentRef.el.innerHTML = this.state.receipt;
        }
       await this.loadReceipt(true);
       this.notification.add("🔄 Receipt Reset Completed!", {
           type: "success",
       });
    }

    onFontChange(ev) {
        this.state.fontStyle = ev.target.value;
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
        const field = `[[${ev.target.dataset.field}]]`;
        ev.dataTransfer.setData("text/plain", field);
        ev.dataTransfer.effectAllowed = "copy";
        const ghost = document.createElement("div");
        ghost.textContent = field;
        ghost.style.padding = "6px 12px";
        ghost.style.fontSize = "12px";
        ghost.style.fontWeight = "400";
        ghost.style.background = "#e8f1ff";
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
            this.receiptContentRef.el.classList.remove("drop-highlight");
        }

    onDrop(ev) {
        ev.preventDefault();
        const editor = this.receiptContentRef.el;
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
        }
        else {
            let targetArea = editor.querySelector(".drop-area")
            if (targetArea) {
                targetArea.appendChild(span);
            }
        }
        this.receiptContentRef.el.classList.remove("dragging");
        this.receiptContentRef.el.classList.remove("drop-highlight");
        span.classList.add("added");
        setTimeout(() => span.classList.remove("added"), 400);
    }
}
registry.category("actions").add("pos_receipt_layout_client_action", PosReceiptLayoutClientAction);