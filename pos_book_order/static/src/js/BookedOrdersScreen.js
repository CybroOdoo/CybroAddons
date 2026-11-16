/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, proxy, useProps, t } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class BookedOrdersScreen extends Component {
/**
* Custom POS screen used to display booked orders and
* convert them into active POS orders for payment.
*/
    static template = "pos_book_order.BookedOrdersScreen";
    props = useProps({
        data: t.or([t.array(), t.object()]).optional(),
        new_order: t.boolean().optional(false),
        booked_order_uuid: t.string().optional(),
    });
    setup() {
        this.pos = usePos();
        this.state = proxy({
            filter: "draft",
            allOrders: Array.isArray(this.props.data) ? this.props.data : [],
        });
        onWillStart(async () => {
            if (!this.pos.config.enable) {
                const order = this.pos.getOrder() || this.pos.addNewOrder();
                this.pos.setOrder(order);
                this.pos.navigate("ProductScreen", { orderUuid: order?.uuid });
                return;
            }
            if (!this.props.data) {
                const orders = await this.pos.data.call("book.order", "all_orders", ["all"]);
                this.state.allOrders = orders || [];
            }
        });
    }
    get orders() {
        if (this.state.filter === "all") {
            return this.state.allOrders;
        }
        return this.state.allOrders.filter((o) => (o.state || "draft") === this.state.filter);
    }
    setFilter(filter) {
        this.state.filter = filter;
    }
    back() {
        const order = this.pos.getOrder() || this.pos.addNewOrder();
        this.pos.setOrder(order);
        this.pos.navigate("ProductScreen", { orderUuid: order?.uuid });
    }
    orderDone() {
        if (this.props.booked_order_uuid) {
            const bookedOrder = this.pos.models["pos.order"]?.getBy("uuid", this.props.booked_order_uuid);
            if (bookedOrder && !bookedOrder.finalized) {
                this.pos.removeOrder(bookedOrder);
            }
        }
        const order = this.pos.addNewOrder();
        this.pos.setOrder(order);
        this.pos.navigate("ProductScreen", { orderUuid: order?.uuid });
    }
    async _Confirm(ev) {
        await this.pos.data.call("book.order", "action_confirm", [ev.id], {});
        ev.state = "confirmed";

        // Find if this order is already open in the POS tabs
        const openOrders = this.pos.models["pos.order"]?.getAll() || [];
        let order = openOrders.find(
            (o) =>
                (ev.pos_order_uid && (o.uuid === ev.pos_order_uid || o.uid === ev.pos_order_uid || o.name === ev.pos_order_uid)) ||
                o.booking_ref_id === ev.id ||
                o.booking_ref_id === ev.name ||
                o.booking_ref_name === ev.name ||
                o.uiState?.booking_ref_id === ev.id ||
                o.uiState?.booking_ref_id === ev.name ||
                o.uiState?.booking_ref_name === ev.name
        );

        if (order) {
            // Reuse the existing order tab, no duplicate tab or lines
            this.pos.setOrder(order);
        } else {
            // Check if current order is empty, otherwise create a new order
            order = this.pos.getOrder();
            if (!order || order.lines.length > 0) {
                order = this.pos.addNewOrder();
            }
            this.pos.setOrder(order);

            if (ev.partner_id) {
                let partner = this.pos.models["res.partner"].get(ev.partner_id);
                if (!partner) {
                    await this.pos.data.read("res.partner", [ev.partner_id]);
                    partner = this.pos.models["res.partner"].get(ev.partner_id);
                }
                if (partner) {
                    order.setPartner(partner);
                }
            }
            if (ev.products && ev.products.length && order.lines.length === 0) {
                for (const p of ev.products) {
                    let product = this.pos.models["product.product"].get(p.id);
                    if (!product) {
                        await this.pos.data.read("product.product", [p.id]);
                        product = this.pos.models["product.product"].get(p.id);
                    }
                    if (product) {
                        const template = product.product_tmpl_id || this.pos.models["product.template"].get(product.product_tmpl_id?.id || product.product_tmpl_id);
                        await this.pos.addLineToOrder({
                            product_id: product,
                            product_tmpl_id: template,
                            qty: p.qty,
                            price_unit: p.price,
                        }, order, {}, false);
                    }
                }
            }
        }

        order.is_booked = true;
        order.is_confirmed_booking = true;
        ev.pos_reference = order.pos_reference;
        order.booked_data = ev;
        order.booking_ref_id = ev.id;
        order.booking_ref_name = ev.name;
        if (order.uiState) {
            order.uiState.is_booked = true;
            order.uiState.is_confirmed_booking = true;
            order.uiState.booked_data = ev;
            order.uiState.booking_ref_id = ev.id;
            order.uiState.booking_ref_name = ev.name;
        }

        this.pos.navigate("ProductScreen", { orderUuid: order?.uuid });
    }
}

registry.category("pos_pages").add("BookedOrdersScreen", {
    name: "BookedOrdersScreen",
    component: BookedOrdersScreen,
    route: `/pos/ui/${odoo.pos_config_id}/bookorder`,
    params: {},
});