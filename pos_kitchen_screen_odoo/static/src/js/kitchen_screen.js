/** @odoo-module */
import { registry } from "@web/core/registry";
const { Component, onMounted, onWillUnmount, useState } = owl;
import { useService } from "@web/core/utils/hooks";

class KitchenScreenDashboard extends Component {
    setup() {
        super.setup();

        // Services
        this.action = useService("action");
        this.rpc = this.env.services.rpc;
        this.orm = useService("orm");
        this.busService = useService("bus_service");

        // Method binding
        this.getCurrentShopId = this.getCurrentShopId.bind(this);
        this.loadOrders = this.loadOrders.bind(this);
        this.startCountdown = this.startCountdown.bind(this);
        this.updateCountdownState = this.updateCountdownState.bind(this);
        this.onPosOrderCreation = this.onPosOrderCreation.bind(this);
        this.accept_order = this.accept_order.bind(this);
        this.done_order = this.done_order.bind(this);
        this.cancel_order = this.cancel_order.bind(this);
        this.accept_order_line = this.accept_order_line.bind(this);
        this.forceRefresh = this.forceRefresh.bind(this);

        // Stage change methods
        this.ready_stage = (e) => this.state.stages = 'ready';
        this.waiting_stage = (e) => this.state.stages = 'waiting';
        this.draft_stage = (e) => this.state.stages = 'draft';

        // Initialization
        this.currentShopId = this.getCurrentShopId();
        this.channel = `pos_order_created_${this.currentShopId}`;
        this.countdownIntervals = {};

        // State management
        this.state = useState({
            order_details: [],
            shop_id: this.currentShopId,
            stages: 'draft',
            draft_count: 0,
            waiting_count: 0,
            ready_count: 0,
            lines: [],
            prepare_times: [],
            countdowns: {},
            isLoading: false
        });

        // Component lifecycle
        onMounted(() => {
            this.busService.addChannel(this.channel);
            this.busService.subscribe('notification', this.onPosOrderCreation);
            this.loadOrders();

            this.autoRefreshInterval = setInterval(() => {
                this.loadOrders();
            }, 30000);
        });

        onWillUnmount(() => {
            this.busService.deleteChannel(this.channel);
            this.busService.unsubscribe('notification', this.onPosOrderCreation);
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
            }
            Object.values(this.countdownIntervals).forEach(interval => {
                clearInterval(interval);
            });
            this.countdownIntervals = {};
        });
    }

    getCurrentShopId() {
        let session_shop_id;
        if (this.props.action?.context?.default_shop_id) {
            sessionStorage.setItem('shop_id', this.props.action.context.default_shop_id);
            session_shop_id = this.props.action.context.default_shop_id;
        } else {
            session_shop_id = sessionStorage.getItem('shop_id');
        }
        return parseInt(session_shop_id, 10) || 0;
    }

    async loadOrders() {
        if (this.state.isLoading) return;

        try {
            this.state.isLoading = true;
            const result = await this.orm.call("pos.order", "get_details", [this.currentShopId]);

            this.state.order_details = result.orders || [];
            this.state.lines = result.order_lines || [];

            const activeOrders = this.state.order_details.filter(order => {
                const configMatch = Array.isArray(order.config_id) ?
                    order.config_id[0] === this.currentShopId :
                    order.config_id === this.currentShopId;
                return configMatch && order.order_status !== 'cancel' && order.state !== 'cancel';
            });
            const productIds = [...new Set(this.state.lines.map(line => line.product_id[0]))];
            if (productIds.length) {
                const overTimes = await this.orm.call(
                    "product.product",
                    "search_read",
                    [[["id", "in", productIds]], ["id", "prepair_time_minutes"]]
                );

                this.state.prepare_times = overTimes.map(item => ({
                    ...item,
                    prepare_time: !item.prepair_time_minutes ? "00:00:00" :
                        typeof item.prepair_time_minutes === 'number' ?
                        parseFloat(item.prepair_time_minutes.toFixed(2)) :
                        item.prepair_time_minutes
                }));
            }
            this.state.draft_count = activeOrders.filter(o => o.order_status === 'draft').length;
            this.state.waiting_count = activeOrders.filter(o => o.order_status === 'waiting').length;
            this.state.ready_count = activeOrders.filter(o => o.order_status === 'ready').length;

            activeOrders.forEach(order => {
                if (order.order_status === 'waiting' && order.avg_prepare_time) {
                    if (!this.countdownIntervals[order.id]) {
                        this.startCountdown(order.id, order.avg_prepare_time);
                    }
                } else if (order.order_status === 'ready') {
                    this.updateCountdownState(order.id, 0, true);
                    if (this.countdownIntervals[order.id]) {
                        clearInterval(this.countdownIntervals[order.id]);
                        delete this.countdownIntervals[order.id];
                    }
                }
            });
        } catch (error) {
            console.error("Error loading orders:", error);
        } finally {
            this.state.isLoading = false;
        }
    }

    async startCountdown(orderId, timeString,config_id) {
        if (this.countdownIntervals[orderId]) {
            clearInterval(this.countdownIntervals[orderId]);
        }

        const [minutes, seconds] = timeString.toFixed(2).split('.').map(Number);
        let totalSeconds = minutes * 60 + seconds;

        this.updateCountdownState(orderId, totalSeconds, false);

        this.countdownIntervals[orderId] = setInterval(async () => {
            totalSeconds--;
            this.updateCountdownState(orderId, totalSeconds, false);
            if (totalSeconds <= 0) {
                try {

                    let orderData = await this.orm.call(
                        'kitchen.screen',
                        'search_read',
                        [
                            [["pos_config_id", "=", config_id[0]]],
                            ["is_preparation_complete"]
                        ]
                    );
                    clearInterval(this.countdownIntervals[orderId]);
                    delete this.countdownIntervals[orderId];
                    this.updateCountdownState(orderId, 0, true);
                    if (orderData[0].is_preparation_complete === true){
                        this.done_order({ target: { value: orderId.toString() } });
                    }

                } catch (error) {
                    console.error("Error fetching order data:", error);
                    // Handle error appropriately
                }
            }
        }, 1000);
    }

    updateCountdownState(orderId, totalSeconds, isCompleted = false) {
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        this.state.countdowns = {
            ...this.state.countdowns,
            [orderId]: {
                minutes,
                seconds,
                isCompleted
            }
        };
    }

    onPosOrderCreation(message) {
        if (!message || message.config_id !== this.currentShopId) {
            return;
        }

        const relevantMessages = [
            'pos_order_created',
            'pos_order_updated',
            'pos_order_paid',
            'pos_order_accepted',
            'pos_order_cancelled',
            'pos_order_completed',
            'pos_order_line_updated'
        ];

        if ((message.res_model === "pos.order" || message.res_model === "pos.order.line") &&
            relevantMessages.includes(message.message)) {
            this.loadOrders();
        }
    }

    async accept_order(e) {
        const orderId = Number(e.target.value);
        try {
            await this.orm.call("pos.order", "order_progress_draft", [orderId]);

            const order = this.state.order_details.find(o => o.id === orderId);
            if (order) {
                order.order_status = 'waiting';
                if (order.avg_prepare_time) {
                    this.startCountdown(orderId, order.avg_prepare_time, order.config_id);
                }
            }

            setTimeout(() => this.loadOrders(), 500);
        } catch (error) {
            console.error("Error accepting order:", error);
        }
    }

    async done_order(e) {
        const orderId = Number(e.target.value);
        try {
            await this.orm.call("pos.order", "order_progress_change", [orderId]);

            const order = this.state.order_details.find(o => o.id === orderId);
            if (order) {
                order.order_status = 'ready';
                this.updateCountdownState(orderId, 0, true);
                if (this.countdownIntervals[orderId]) {
                    clearInterval(this.countdownIntervals[orderId]);
                    delete this.countdownIntervals[orderId];
                }
            }

            setTimeout(() => this.loadOrders(), 500);
        } catch (error) {
            console.error("Error completing order:", error);
        }
    }

    async cancel_order(e) {
        const orderId = Number(e.target.value);
        try {
            await this.orm.call("pos.order", "order_progress_cancel", [orderId]);

            const order = this.state.order_details.find(o => o.id === orderId);
            if (order) {
                order.order_status = 'cancel';
            }

            setTimeout(() => this.loadOrders(), 500);
        } catch (error) {
            console.error("Error cancelling order:", error);
        }
    }

    async accept_order_line(e) {
        const lineId = Number(e.target.value);
        try {
            await this.orm.call("pos.order.line", "order_progress_change", [lineId]);

            const line = this.state.lines.find(l => l.id === lineId);
            if (line) {
                line.order_status = line.order_status === 'ready' ? 'waiting' : 'ready';
            }

            setTimeout(() => this.loadOrders(), 500);
        } catch (error) {
            console.error("Error updating order line:", error);
        }
    }

    get filteredOrders() {
        return this.state.order_details.filter(order => {
            const configMatch = Array.isArray(order.config_id) ?
                order.config_id[0] === this.currentShopId :
                order.config_id === this.currentShopId;
            const stageMatch = order.order_status === this.state.stages;
            return configMatch && stageMatch && order.order_status !== 'cancel';
        });
    }

    forceRefresh() {
        this.loadOrders();
    }
}

KitchenScreenDashboard.template = 'KitchenCustomDashBoard';
registry.category("actions").add("kitchen_custom_dashboard_tags", KitchenScreenDashboard);