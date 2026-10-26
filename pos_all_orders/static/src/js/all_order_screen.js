/** @odoo-module **/
import { Component, proxy, onWillStart, useProps, t } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";

export class CustomALLOrdrScreen extends Component {
    static template = "pos_all_orders.CustomALLOrdrScreen";
    static storeOnOrder = false;

    props = useProps({
        orders: t.any().optional(),
        orderUuid: t.string().optional(),
    });

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.state = proxy({
            orders: this.props.orders || [],
            searchWord: "",
            loading: !this.props.orders || !this.props.orders.length,
        });

        onWillStart(async () => {
            if (!this.props.orders || !this.props.orders.length) {
                await this.loadOrders();
            }
        });
    }

    async loadOrders() {
        this.state.loading = true;
        try {
            const session = this.pos.session?.id || odoo.pos_session_id;
            const orders = await this.orm.call(
                "pos.session",
                "get_pos_all_orders",
                [{ session: session }],
                {}
            );
            this.state.orders = orders || [];
        } catch (_error) {
            this.state.orders = [];
        } finally {
            this.state.loading = false;
        }
    }

    get filteredOrders() {
        const query = (this.state.searchWord || "").trim().toLowerCase();
        if (!query) {
            return this.state.orders;
        }
        return this.state.orders.filter((order) => {
            const posRef = (order.pos_reference || "").toLowerCase();
            const name = (order.name || "").toLowerCase();
            const partner = (order.partner_id || "").toLowerCase();
            const date = (order.date_order || "").toLowerCase();
            const session = (order.session || "").toLowerCase();
            return (
                posRef.includes(query) ||
                name.includes(query) ||
                partner.includes(query) ||
                date.includes(query) ||
                session.includes(query)
            );
        });
    }

    formatOrderTotal(amount) {
        return this.pos.formatCurrency(amount || 0);
    }

    getStatusBadgeClass(state) {
        switch (state) {
            case "paid":
            case "done":
                return "text-bg-success";
            case "invoiced":
                return "text-bg-info";
            case "draft":
                return "text-bg-warning";
            case "cancel":
                return "text-bg-danger";
            default:
                return "text-bg-secondary";
        }
    }

    onSearchInput(ev) {
        this.state.searchWord = ev.target.value;
    }

    clearSearch() {
        this.state.searchWord = "";
    }

    back() {
        // on clicking the back button it will redirect to Product screen
        try {
            const order =
                (this.props.orderUuid && this.pos.models?.["pos.order"]?.getBy("uuid", this.props.orderUuid)) ||
                (this.props.orderUuid && this.pos.models?.["pos.order"]?.find?.((o) => o.uuid === this.props.orderUuid)) ||
                this.pos.getOrder() ||
                this.pos.getOpenOrders?.()?.[0] ||
                this.pos.openOrder ||
                this.pos.addNewOrder();

            if (order) {
                this.pos.setOrder(order);
                const screen = order.getScreenData?.();
                if (!screen || screen.name === "CustomALLOrdrScreen") {
                    order.setScreenData?.({ name: "ProductScreen", props: { orderUuid: order.uuid } });
                }
                this.pos.navigateToOrderScreen(order);
            } else {
                this.pos.navigate("ProductScreen");
            }
        } catch (_error) {
            if (this.pos.router?.back) {
                this.pos.router.back();
            } else {
                window.history.back();
            }
        }
    }
}

registry.category("pos_pages").add("CustomALLOrdrScreen", {
    name: "CustomALLOrdrScreen",
    component: CustomALLOrdrScreen,
    route: `/pos/ui/${odoo.pos_config_id}/all_orders`,
    params: {},
});
