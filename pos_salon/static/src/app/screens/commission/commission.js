import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatSalonAmount } from "@pos_salon/app/utils/salon_currency";

export class CommissionScreen extends Component {
    static template = "pos_salon.CommissionScreen";

    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = useState({
            scope: "today",
            loading: true,
            error: null,
            allowed: true,
            message: "",
            rows: [],
            totals: [],
            grandAmount: 0,
            grandCommission: 0,
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const result = await this.orm.call(
                "salon.booking", "get_commission_data",
                [this.pos.config.id, this.state.scope]
            );
            this.state.allowed = result.allowed;
            this.state.message = result.message || "";
            this.state.rows = result.rows || [];
            this.state.totals = result.totals || [];
            this.state.grandAmount = result.grand_amount || 0;
            this.state.grandCommission = result.grand_commission || 0;
        } catch (err) {
            this.state.error = err.data?.message || err.message || "Could not load commission";
        } finally {
            this.state.loading = false;
        }
    }

    async setScope(scope) {
        this.state.scope = scope;
        await this.load();
    }

    formatMoney(value) {
        return formatSalonAmount(this.pos, value);
    }

    formatDate(dateStr) {
        if (!dateStr) return "-";
        return new Date(dateStr).toLocaleDateString(undefined, {
            year: "numeric", month: "short", day: "numeric",
        });
    }

    back() {
        this.pos.router.navigate("SalonScreen");
    }
}

registry.category("pos_pages").add("CommissionScreen", {
    name: "CommissionScreen",
    component: CommissionScreen,
    route: `/pos/ui/${odoo.pos_config_id}/commission`,
});