/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { Component, useRef } from "@odoo/owl";

export class MagnifyProductPopup extends Component {
    static template = "MagnifyProductPopup";
    static components = { Dialog };

    setup() {
        this.imageRef = useRef("imageRef");

        this.zoomLevel = 1;
        this.isPanning = false;
        this.startX = 0;
        this.startY = 0;
        this.translateX = 0;
        this.translateY = 0;
    }

    onZoom(ev) {
        ev.preventDefault();

        const img = this.imageRef.el;
        if (!img) return;

        const zoomStep = 0.1;
        this.zoomLevel += ev.deltaY < 0 ? zoomStep : -zoomStep;
        this.zoomLevel = Math.min(Math.max(this.zoomLevel, 1), 3);

        if (this.zoomLevel === 1) {
            this.translateX = 0;
            this.translateY = 0;
        }

        this.applyTransform();
    }

    startPan(ev) {
        if (this.zoomLevel <= 1) return;

        this.isPanning = true;
        this.startX = ev.clientX - this.translateX;
        this.startY = ev.clientY - this.translateY;

        this.imageRef.el.style.cursor = "grabbing";
    }

    onPan(ev) {
        if (!this.isPanning) return;

        this.translateX = ev.clientX - this.startX;
        this.translateY = ev.clientY - this.startY;

        this.applyTransform();
    }

    stopPan() {
        this.isPanning = false;
        if (this.imageRef.el) {
            this.imageRef.el.style.cursor = "grab";
        }
    }

    applyTransform() {
        const img = this.imageRef.el;
        img.style.transform = `
            translate(${this.translateX}px, ${this.translateY}px)
            scale(${this.zoomLevel})
        `;
    }
}
