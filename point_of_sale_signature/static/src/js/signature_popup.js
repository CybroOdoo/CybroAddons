/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";
import { onMounted } from "@odoo/owl";

export class SignaturePopup extends AbstractAwaitablePopup {
    static template = "point_of_sale_signature.SignaturePopup";
    static components = {};

    setup() {
        super.setup();

        this.isDrawing = false;
        this.canvas = null;
        this.ctx = null;

        onMounted(() => {
            this._initCanvas();
        });
    }

    _initCanvas() {
        this.canvas = document.querySelector("canvas");
        if (!this.canvas) {
            return;
        }

        this.ctx = this.canvas.getContext("2d");
        this.ctx.lineWidth = 2;
        this.ctx.lineCap = "round";

        this.canvas.addEventListener("mousedown", this._startDraw.bind(this));
        this.canvas.addEventListener("mousemove", this._draw.bind(this));
        window.addEventListener("mouseup", this._stopDraw.bind(this));

        this.canvas.addEventListener("touchstart", this._startDraw.bind(this), { passive: false });
        this.canvas.addEventListener("touchmove", this._draw.bind(this), { passive: false });
        window.addEventListener("touchend", this._stopDraw.bind(this));
    }

    _getPos(ev) {
        const rect = this.canvas.getBoundingClientRect();
        const e = ev.touches ? ev.touches[0] : ev;

        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        };
    }

    _startDraw(ev) {
        ev.preventDefault();
        this.isDrawing = true;

        const pos = this._getPos(ev);
        this.ctx.beginPath();
        this.ctx.moveTo(pos.x, pos.y);
    }

    _draw(ev) {
        if (!this.isDrawing) return;
        ev.preventDefault();

        const pos = this._getPos(ev);
        this.ctx.lineTo(pos.x, pos.y);
        this.ctx.stroke();
    }

    _stopDraw() {
        this.isDrawing = false;
    }
    clearSignature() {
        const canvas = document.querySelector("canvas");
        const ctx = this.ctx;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Optional: reset background to white
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    confirm() {
        const dataUrl = this.canvas.toDataURL("image/png");
        const base64 = dataUrl.split(",")[1];
        this.props.resolve({ confirmed: true, payload: base64 });
        super.confirm();
    }
}

registry.category("popups").add("SignaturePopup", SignaturePopup);
