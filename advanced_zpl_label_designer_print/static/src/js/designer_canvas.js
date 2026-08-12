/** @odoo-module **/

export class ZplDesignerCanvas {
    constructor(canvasId, width = 500, height = 600, onSelection = null) {
        this.fabric = window.fabric;
        this.canvas = new this.fabric.Canvas(canvasId, {
            width: width,
            height: height,
            backgroundColor: '#ffffff',
            selection: true
        });

        if (onSelection) {
            this.canvas.on('selection:created', (e) => onSelection(e.selected[0]));
            this.canvas.on('selection:updated', (e) => onSelection(e.selected[0]));
            this.canvas.on('selection:cleared', () => onSelection(null));
        }
    }

    updateObject(obj, props) {
        if (!obj) return;

        // If it's a barcode/qrcode group, update the text label inside
        if (obj.type === 'group' && props.text !== undefined) {
            const label = obj._objects && obj._objects[1];
            if (label) label.set('text', props.text);
        }

        obj.set(props);
        this.canvas.renderAll();
    }

    addText(text, x, y, id = null, field_id = null) {
        const textObj = new this.fabric.IText(text, {
            left: x,
            top: y,
            fontSize: 25,
            fontFamily: 'Courier',
            fill: '#000000',
            db_id: id,// Store the database ID if it exists
            field_id: field_id
        });
        this.canvas.add(textObj);
        this.canvas.renderAll();
    }

    addBarcode(value, type, x, y, id = null, field_id = null) {
        const rect = new this.fabric.Rect({ width: 150, height: 60, fill: '#000' });
        const label = new this.fabric.Text(value, { fontSize: 15, top: 65, fill: '#000' });
        const group = new this.fabric.Group([rect, label], {
            left: x,
            top: y,
            db_id: id,
            field_id: field_id
        });
        group.set('zplType', 'barcode');
        this.canvas.add(group);
        this.canvas.renderAll();
    }

    addRect(x, y, w, h, id = null) {
        const rect = new this.fabric.Rect({
            left: x,
            top: y,
            width: w,
            height: h,
            fill: 'transparent',
            stroke: '#000',
            strokeWidth: 2,
            db_id: id
        });
        rect.set('zplType', 'rect');
        this.canvas.add(rect);
        this.canvas.renderAll();
    }

    addQRCode(value, x, y, id = null, field_id = null) {
        const rect = new this.fabric.Rect({ width: 80, height: 80, fill: '#000' });
        const label = new this.fabric.Text("QR", { fontSize: 20, top: 30, left: 25, fill: '#fff' });
        const group = new this.fabric.Group([rect, label], {
            left: x,
            top: y,
            db_id: id,
            field_id: field_id
        });
        group.set('zplType', 'qrcode');
        this.canvas.add(group);
        this.canvas.renderAll();
    }

    addLine(x, y, w, h, id = null) {
        const line = new this.fabric.Rect({
            left: x,
            top: y,
            width: w || 100,
            height: h || 2,
            fill: '#000',
            db_id: id
        });
        line.set('zplType', 'line');
        this.canvas.add(line);
        this.canvas.renderAll();
    }

    deleteSelected() {
        const activeObjects = this.canvas.getActiveObjects();
        if (activeObjects.length) {
            activeObjects.forEach(obj => {
                this.canvas.remove(obj);
            });
            this.canvas.discardActiveObject();
            this.canvas.renderAll();
        }
    }

    // New: Clear the canvas
    clear() {
        this.canvas.clear();
        this.canvas.setBackgroundColor('#ffffff', this.canvas.renderAll.bind(this.canvas));
    }
}