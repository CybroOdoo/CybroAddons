import { Component, onMounted, onWillUnmount, proxy } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class ScaleScreen extends Component {
    static template = "pos_weight_manual.ScaleScreenManual";
    static components = { Dialog };

    static props = {
        getPayload: { type: Function, optional: true },
        productName: { type: String, optional: true },
        uomName: { type: String, optional: true },
        uomRounding: { type: Number, optional: true },
        productPrice: { type: Number, optional: true },
        close: { type: Function, optional: true },
    };

    setup() {
        this.pos = usePos();
        this.hardwareProxy = this.pos?.hardware_proxy || this.pos?.scale;

        this.state = proxy({
            weight: 0,
            tare: 0,
            manualOverride: false,
        });

        useHotkey("enter", () => this.confirm());
        useHotkey("escape", () => this.props.close?.());

        onMounted(this.onMounted);
        onWillUnmount(this.onWillUnmount);
    }

    onMounted() {
        this._readScale();
        const inputEl = document.querySelector(".pos-manual-weight-input");
        if (inputEl) {
            inputEl.focus();
            inputEl.select();
        }
    }

    onWillUnmount() {
        this.shouldRead = false;
    }

    confirm() {
        if (this.netWeight > 0) {
            this.props.getPayload?.(this.netWeight);
        }
        this.props.close?.();
    }

    _readScale() {
        this.shouldRead = true;
        this._setWeight();
    }

    async _setWeight() {
        if (!this.shouldRead || this.state.manualOverride) {
            return;
        }

        try {
            if (this.hardwareProxy?.readScale) {
                const scaleWeight = await this.hardwareProxy.readScale();
                this.state.weight = scaleWeight || 0;
            } else if (this.hardwareProxy?.readWeight) {
                await this.hardwareProxy.readWeight();
                this.state.weight = this.hardwareProxy.weight || 0;
            }
        } catch {
            // Hardware read unavailable; allow manual weight entry
        }
    }

    get netWeight() {
        const rounding = this.props.uomRounding && this.props.uomRounding > 0
            ? this.props.uomRounding
            : 0.01;
        const weight = round_pr(this.state.weight || 0, rounding);
        const decimals = Math.max(0, Math.ceil(Math.log10(1.0 / rounding)));
        const rounded = weight.toFixed(decimals);
        return Math.max(0, parseFloat(rounded) - parseFloat(this.state.tare || 0));
    }

    get unitPriceString() {
        return this.pos.formatCurrency(this.props.productPrice || 0);
    }

    get computedPriceString() {
        return this.pos.formatCurrency(this.netWeight * (this.props.productPrice || 0));
    }

    handleInputChange(ev) {
        if (ev.target.validity?.badInput) {
            return;
        }
        if (ev.target.value === "") {
            this.state.weight = 0;
            this.state.manualOverride = true;
            return;
        }
        const value = parseFloat(ev.target.value);
        if (!isNaN(value)) {
            this.state.weight = value;
            this.state.manualOverride = true;
        }
    }
}