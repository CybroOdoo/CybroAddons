import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class ScaleScreen extends Component {
    static template = "pos_weight_manual.ScaleScreenManual";
    static components = { Dialog };

    static props = {
        getPayload: Function,
        productName: String,
        uomName: String,
        uomRounding: Number,
        productPrice: Number,
        close: Function,
    };

    setup() {
        this.pos = usePos();
        this.hardwareProxy = useService("hardware_proxy");

        this.state = useState({
            weight: 0,
            tare: 0,
            tareLoading: false,
            manualOverride: false,
        });

        onMounted(this.onMounted);
        onWillUnmount(this.onWillUnmount);
    }

    onMounted() {
        this._readScale();
    }

    onWillUnmount() {
        this.shouldRead = false;
    }

    confirm() {
        this.props.getPayload(this.netWeight);
        this.props.close();
    }

    _readScale() {
        this.shouldRead = true;
        this._setWeight();
    }

    async _setWeight() {
        if (!this.shouldRead || this.state.manualOverride) return;

        try {
            const scaleWeight = await this.hardwareProxy.readScale();
            this.state.weight = scaleWeight;
            // Removed this.pos.setScaleWeight(scaleWeight) as it doesn't exist
        } catch (error) {
            console.warn("Scale read error:", error);
        }

        setTimeout(() => this._setWeight(), 500);
    }

    get netWeight() {
        const weight = round_pr(this.state.weight || 0, this.props.uomRounding);
        const rounded = weight.toFixed(
            Math.ceil(Math.log(1.0 / this.props.uomRounding) / Math.log(10))
        );
        return parseFloat(rounded) - parseFloat(this.state.tare || 0);
    }

    get productWeightString() {
        const weight = round_pr(this.state.weight || 0, this.props.uomRounding);
        const weightStr = weight.toFixed(
            Math.ceil(Math.log(1.0 / this.props.uomRounding) / Math.log(10))
        );
        return `${weightStr} ${this.props.uomName || 'Kg'}`;
    }

    get computedPriceString() {
        const priceString = this.env.utils.formatCurrency(this.netWeight * this.props.productPrice);
        // Store the price in a way that doesn't require pos.totalPriceOnScale
        // You can access this via this.computedPriceString when needed
        return priceString;
    }

    async handleTareButtonClick() {
        this.state.tareLoading = true;
        try {
            const tareWeight = await this.hardwareProxy.readScale();
            this.state.tare = tareWeight;
        } catch (error) {
            console.warn("Tare read error:", error);
        }
        setTimeout(() => {
            this.state.tareLoading = false;
        }, 3000);
    }

    handleInputChange(ev) {
        const value = parseFloat(ev.target.value) || 0;
        this.state.weight = value;
        this.state.manualOverride = true;
    }
}