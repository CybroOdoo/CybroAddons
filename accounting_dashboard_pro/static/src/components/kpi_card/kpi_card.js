/** @odoo-module **/

import { Component, onMounted, onPatched, signal, proxy, useProps } from "@odoo/owl";

export class KpiCard extends Component {
    static template = "accounting_dashboard_pro.KpiCard";
    props = useProps();
    amountRef = signal.ref();

    setup() {
        this.infoState = proxy({ show: false });
        onMounted(() => this.animateCount());
        onPatched(() => this.animateCount());
    }

    onInfoEnter(ev) {
        ev.stopPropagation();
        this.infoState.show = true;
    }

    onInfoLeave(ev) {
        this.infoState.show = false;
    }

    animateCount() {
        const el = this.amountRef();
        if (!el) return;
        const target = this.props.amount || 0;
        const duration = 700;
        const start = performance.now();

        const step = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;

            if (this.props.useRaw) {
                el.textContent = Math.round(current) + (this.props.rawSuffix || '');
            } else {
                el.textContent = this.props.formatCurrency(current);
            }

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }

    get changeClass() {
        const pct = this.props.changePct || 0;
        if (pct > 0) return "positive";
        if (pct < 0) return "negative";
        return "neutral";
    }

    get changeIcon() {
        const pct = this.props.changePct || 0;
        return pct > 0 ? "arrow_upward" : pct < 0 ? "arrow_downward" : "remove";
    }

    get hasPrev() {
        return this.props.prevAmount !== undefined && this.props.prevAmount !== null;
    }

    get infoLines() {
        return (this.props.info || "").split("\n").filter(Boolean);
    }
}
