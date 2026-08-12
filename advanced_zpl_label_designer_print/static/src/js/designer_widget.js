/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onMounted, useState, onWillStart, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ZplDesignerCanvas } from "./designer_canvas";

export class ZplDesignerWidget extends Component {
    static template = "zpl_label_designer.DesignerWidget";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            fields: [],
            selectedFieldId: "",
            searchText: "",
            showDropdown: false,
            selectedObject: null,
        });

        onWillStart(async () => {
            await this.loadModelFields(this.props.record);
        });

        onMounted(async () => {
            this.initCanvas();

            const clickOutside = (ev) => {
                if (this.state.showDropdown && !ev.target.closest('.o_zpl_field_selector_wrapper')) {
                    this.state.showDropdown = false;
                }
            };
            window.addEventListener('click', clickOutside);
            return () => window.removeEventListener('click', clickOutside);
        });

        let lastModelId = this.extractModelId(this.props.record);
        useEffect(
            () => {
                const currentModelId = this.extractModelId(this.props.record);
                if (currentModelId && currentModelId !== lastModelId) {
                    lastModelId = currentModelId;
                    this.loadModelFields(this.props.record);
                }
            },
            () => [this.props.record.data.model_id]
        );
    }

    getFilteredFields() {
        if (!this.state.searchText) return this.state.fields;
        const search = this.state.searchText.toLowerCase();
        return this.state.fields.filter(f =>
            f.name.toLowerCase().includes(search) ||
            f.field_description.toLowerCase().includes(search)
        );
    }

    selectField(field) {
        this.state.searchText = `${field.field_description} (${field.name})`;
        this.state.showDropdown = false;
    }

    updateSelectedObjectProperty(prop, value) {
        if (!this.state.selectedObject) return;

        const raw = this.state.selectedObject._raw;
        const updates = {};

        if (prop === 'field_id') {
            const fieldId = parseInt(value) || false;
            updates.field_id = fieldId;
            this.state.selectedObject.field_id = fieldId;

            // Update placeholder text if linked to field
            if (fieldId) {
                const field = this.state.fields.find(f => f.id === fieldId);
                if (field) {
                    updates.text = field.field_description;
                    this.state.selectedObject.text = field.field_description;
                }
            }
        } else if (prop === 'text') {
            updates.text = value;
            this.state.selectedObject.text = value;
        } else if (prop === 'fontSize' || prop === 'strokeWidth' || prop === 'rounding') {
            const val = parseInt(value) || 0;
            updates[prop] = val;
            this.state.selectedObject[prop] = val;
        } else {
            updates[prop] = value;
            this.state.selectedObject[prop] = value;
        }

        this.canvas.updateObject(raw, updates);
    }

    extractModelId(record) {
        if (!record) return false;

        // Try common data paths (Direct, Root, Changes)
        let modelData = (record.data && record.data.model_id) ||
            (record.model && record.model.root && record.model.root.data && record.model.root.data.model_id) ||
            (record._changes && record._changes.model_id);

        if (!modelData) return false;

        // Parse ID (Handle Array, Object, or Raw)
        let finalId = Array.isArray(modelData) ? modelData[0] :
            (typeof modelData === 'object' ? (modelData.resId || modelData.id || (modelData.data && modelData.data.id)) : modelData);

        return finalId ? (parseInt(finalId) || finalId) : false;
    }

    async loadModelFields(record) {
        const modelId = this.extractModelId(record);
        if (!modelId) {
            this.state.fields = [];
            return;
        }

        try {
            const fields = await this.orm.searchRead(
                "ir.model.fields",
                [["model_id", "=", modelId], ["ttype", "not in", ["one2many", "many2many", "binary"]]],
                ["name", "field_description"]
            );
            this.state.fields = fields.sort((a, b) =>
                (a.field_description || a.name).localeCompare(b.field_description || b.name)
            );
        } catch (e) {
            this.state.fields = [];
        }
    }

    onAddField() {
        const field = this._getSelectedField();
        if (field) {
            this.canvas.addText(field.field_description, 50, 50, null, field.id);
            this.state.searchText = "";
        }
    }

    onAddBarcodeFromField() {
        const field = this._getSelectedField();
        if (field) {
            this.canvas.addBarcode(field.field_description, 'code128', 50, 50, null, field.id);
            this.state.searchText = "";
        }
    }

    onAddQRCodeFromField() {
        const field = this._getSelectedField();
        if (field) {
            this.canvas.addQRCode(field.field_description, 50, 50, null, field.id);
            this.state.searchText = "";
        }
    }

    _getSelectedField() {
        if (!this.state.searchText) {
            this.notification.add("Please select a field first.", { type: "warning" });
            return null;
        }

        const field = this.state.fields.find(f =>
            `${f.field_description} (${f.name})` === this.state.searchText ||
            f.field_description === this.state.searchText ||
            f.name === this.state.searchText
        );

        if (!field) {
            this.notification.add("Selected field not found in list.", { type: "danger" });
            return null;
        }
        return field;
    }

    async initCanvas() {
        this.canvas = new ZplDesignerCanvas("zpl_designer_canvas", 500, 600, (obj) => {
            if (obj) {
                this.state.selectedObject = {
                    type: obj.zplType || (obj.type === 'i-text' ? 'text' : (obj.type === 'rect' ? 'rect' : obj.type)),
                    text: obj.text || (obj._objects && obj._objects[1] ? obj._objects[1].text : ""),
                    field_id: obj.field_id || false,
                    barcode_type: obj.barcode_type || 'code128',
                    fontSize: obj.fontSize || 25,
                    strokeWidth: obj.strokeWidth || 1,
                    rounding: obj.rounding || 0,
                    _raw: obj
                };
            } else {
                this.state.selectedObject = null;
            }
        });

        // Use resId for saved records, or data.id for new records
        const recordId = this.props.record.resId || this.props.record.data.id;

        if (recordId) {
            const elements = await this.orm.searchRead(
                "zpl.label.element",
                [["template_id", "=", recordId]],
                ["name", "x_pos", "y_pos", "width", "height", "type", "field_id", "thickness", "rounding", "font_size", "barcode_type"]
            );

            elements.forEach(el => {
                const f_id = Array.isArray(el.field_id) ? el.field_id[0] : el.field_id;

                if (el.type === 'text') {
                    this.canvas.addText(el.name, el.x_pos, el.y_pos, el.id, f_id);
                    const obj = this.canvas.canvas.getObjects().slice(-1)[0];
                    if (obj && el.font_size) {
                        obj.set('fontSize', el.font_size);
                    }
                } else if (el.type === 'barcode') {
                    this.canvas.addBarcode(el.name, el.barcode_type || 'code128', el.x_pos, el.y_pos, el.id, f_id);
                    const obj = this.canvas.canvas.getObjects().slice(-1)[0];
                    if (obj) {
                        obj.set('barcode_type', el.barcode_type || 'code128');
                        if (el.font_size) {
                            const rect = obj._objects && obj._objects[0];
                            if (rect) rect.set('height', el.font_size);
                            obj.set('fontSize', el.font_size);
                        }
                    }
                } else if (el.type === 'qrcode') {
                    this.canvas.addQRCode(el.name, el.x_pos, el.y_pos, el.id, f_id);
                } else if (el.type === 'line') {
                    this.canvas.addLine(el.x_pos, el.y_pos, el.width, el.height, el.id);
                } else if (el.type === 'rect') {
                    this.canvas.addRect(el.x_pos, el.y_pos, el.width || 100, el.height || 50, el.id);
                    const obj = this.canvas.canvas.getObjects().slice(-1)[0];
                    if (obj) {
                        if (el.thickness) obj.set('strokeWidth', el.thickness);
                        if (el.rounding) obj.set('rounding', el.rounding);
                    }
                }
            });
            this.canvas.canvas.renderAll();
        }
    }

    onAddText() {
        this.canvas.addText("New Text", 50, 50);
    }

    onAddBarcode() {
        this.canvas.addBarcode("123456", "code128", 50, 150);
    }

    onAddRect() {
        this.canvas.addRect(50, 250, 100, 50);
    }

    onAddQRCode() {
        this.canvas.addQRCode("QR Data", 50, 350);
    }

    onAddLine() {
        this.canvas.addLine(50, 450, 200, 2);
    }

    onDeleteSelected() {
        this.canvas.deleteSelected();
    }

    async onSaveDesign() {
        const recordId = this.props.record.resId || this.props.record.data.id;

        if (!recordId) {
            this.notification.add(
                "Please save the Template record (main Odoo Save button) before designing.",
                { type: "danger" }
            );
            return;
        }

        const objects = this.canvas.canvas.getObjects();
        const elements = objects.map(obj => {
            const zplType = obj.zplType || (obj.type === "i-text" ? "text" : "text");
            return {
                db_id: obj.db_id || false,
                name: obj.text || (obj._objects && obj._objects[1] ? obj._objects[1].text : (zplType === 'rect' ? 'Rectangle' : 'Element')),
                x_pos: Math.round(obj.left),
                y_pos: Math.round(obj.top),
                width: Math.round(obj.width * (obj.scaleX || 1)),
                height: Math.round(obj.height * (obj.scaleY || 1)),
                thickness: obj.strokeWidth || 1,
                rounding: obj.rounding || 0,
                font_size: obj.fontSize || 25,
                type: zplType,
                field_id: obj.field_id || null,
                barcode_type: obj.barcode_type || 'code128',
            };
        });

        try {
            const result = await this.orm.call(
                "zpl.label.template",
                "save_design_from_js",
                [recordId, elements]
            );

            if (result) {
                this.notification.add("Design Saved Successfully!", { type: "success" });
                await this.props.record.model.root.load();
            }
        } catch (error) {
            this.notification.add("Error saving design: " + error.message, { type: "danger" });
        }
    }
}

registry.category("fields").add("zpl_designer_widget", {
    component: ZplDesignerWidget,
});