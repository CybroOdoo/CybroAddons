/** @odoo-module **/
import { registry } from "@web/core/registry";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { parseUTCString } from "@point_of_sale/utils";

patch(TicketScreen.prototype, {
    setup() {
        super.setup();

        // Initialize hooks & services
        this.pos = usePos();
        this.orm = useService("orm");

        // Initialize state safely
        if (!this._state) this._state = {};

        // Main synced order state
        if (!this._state.syncedOrders) {
            this._state.syncedOrders = {
                nPerPage: 20,
                currentPage: 1,
                cache: {},
                toShow: [],
                totalCount: 0,
            };
        }

        // UI filter state
        if (!this._state.ui) {
            this._state.ui = { filter: "SYNCED" };
        }

        // Persistent offset tracking
        if (!this.pos.ticketScreenState) {
            this.pos.ticketScreenState = { offsetByDomain: {} };
        }
        if (!this.pos.ticketScreenState.offsetByDomain) {
            this.pos.ticketScreenState.offsetByDomain = {};
        }

        // Cache for partial orders (persistent)
        if (!this._state.partialOrdersCache) {
            this._state.partialOrdersCache = {
                orders: [],
                cache: {},
                totalCount: 0,
            };
        }
    },

    // 1️⃣ Add new filter option "Partial"
    _getFilterOptions() {
        const orderStates = super._getFilterOptions();
        orderStates.set("PARTIAL", { text: _t("Partial") });
        return orderStates;
    },

    // 2️⃣ Handle filter selection
    async onFilterSelected(selectedFilter) {

        if (!this._state.ui) this._state.ui = {};
        this._state.ui.filter = selectedFilter;

        if (selectedFilter === "PARTIAL") {

            // Don’t reset if already cached
            if (this._state.partialOrdersCache.orders.length > 0) {
                this._applyPartialOrdersFromCache();
                this.render();
                return;
            }

            await this._fetchPartialOrders();
        } else {
            await super.onFilterSelected(selectedFilter);
        }
    },

    // 3️⃣ Compute domain for partial orders
    _computePartialOrdersDomain() {
        return [
            ["config_id", "=", this.pos.config.id],
            ["is_partial_payment", "=", true],
            ["state", "not in", ["draft", "cancel"]],
        ];
    },

    // 4️⃣ Fetch Partial Orders
async _fetchPartialOrders() {
    try {
        const domain = this._computePartialOrdersDomain();
        const config_id = this.pos.config.id;

        // proper Odoo RPC call in TicketScreen
        const result = await this.orm.call(
            "pos.order",
            "search_partial_order_ids",
            [],
            {
                config_id,
                domain,
                limit: 30,
                offset: this.pos.ticketScreenState.offsetByDomain[JSON.stringify(domain)] || 0,
            }
        );

        const ordersInfo = result.orders || [];
        const totalCount = result.totalCount || 0;


        const idsToFetch = ordersInfo.map(item => item[0]);

        if (idsToFetch.length > 0) {
            await this.pos.data.read("pos.order", idsToFetch);
        }

        const loadedOrders = idsToFetch
            .map(id => this.pos.models["pos.order"].get(id))
            .filter(o => o);

        const cache = this._state.partialOrdersCache;

        loadedOrders.forEach(order => {
            cache.cache[order.id] = order;
            if (!cache.orders.find(o => o.id === order.id)) {
                cache.orders.push(order);
            }
        });

        cache.totalCount = totalCount;

        this._applyPartialOrdersFromCache();
        this.render();

    } catch (err) {
        console.error("Partial fetch error:", err);
    }
},

    // ✅ Helper to sync cached partial orders to UI
    _applyPartialOrdersFromCache() {
        const cache = this._state.partialOrdersCache;
        this._state.syncedOrders = {
            nPerPage: 20,
            currentPage: 1,
            cache: cache.cache,
            toShow: cache.orders,
            totalCount: cache.totalCount,
        };
    },

    // 5️⃣ Load more partial orders
    async _loadMorePartialOrders() {
        await this._fetchPartialOrders();
    },

    // 6️⃣ Total calculation
    getTotal(order) {
        if (this._state.ui?.filter === "PARTIAL" && order) {
            return typeof order.get_total_with_tax === "function"
                ? order.get_total_with_tax()
                : order.amount_total || 0;
        }
        return super.getTotal(order);
    },

    // 7️⃣ Filtered order list
    getFilteredOrderList() {
        if (this._state.ui?.filter === "PARTIAL") {
            const orders = this._state.syncedOrders?.toShow || [];
            return orders;
        }
        return super.getFilteredOrderList();
    },

    // 8️⃣ Selected order
    getSelectedSyncedOrder() {
        if (this._state.ui?.filter === "PARTIAL") {
            const selectedId = this._state.selectedSyncedOrderId;
            const order = this._state.syncedOrders.cache[selectedId];
            return order || null;
        }
        return super.getSelectedSyncedOrder();
    },

    // 9️⃣ Hide delete button
    shouldHideDeleteButton(order) {
        if (this._state.ui?.filter === "PARTIAL") {
            return true;
        }
        return super.shouldHideDeleteButton(order);
    },

    // 🔟 Prevent delete
    _canDeleteOrder(order) {
        if (this._state.ui?.filter === "PARTIAL") {
            return false;
        }
        return super._canDeleteOrder(order);
    },

    // 1️⃣1️⃣ Handle pagination
    async onNextPage() {
        if (this._state.ui?.filter === "PARTIAL") {
            await this._loadMorePartialOrders();
        } else {
            await super.onNextPage();
        }
    },
});
