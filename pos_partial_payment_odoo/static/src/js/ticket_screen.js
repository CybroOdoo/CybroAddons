/** @odoo-module **/

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { parseUTCString } from "@point_of_sale/utils";

/**
 * Patch for TicketScreen to add filtering and management of partial payments.
 */
patch(TicketScreen.prototype, {
    /**
     * @override
     * Initialize services and state for partial order tracking.
     */
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

    /**
     * Add "Partial" to the available filter options.
     * @override
     * @returns {Map}
     */
    _getFilterOptions() {
        const orderStates = super._getFilterOptions();
        orderStates.set("PARTIAL", { text: _t("Partial") });
        return orderStates;
    },

    /**
     * Handle the selection of the Partial Payment filter.
     * @override
     * @param {String} selectedFilter
     */
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

    /**
     * Compute the search domain specifically for partial orders.
     * @returns {Array}
     */
    _computePartialOrdersDomain() {
        return [
            ["config_id", "=", this.pos.config.id],
            ["is_partial_payment", "=", true],
            ["state", "not in", ["draft", "cancel"]],
        ];
    },

    /**
     * Fetch partial orders from the server and update local state/cache.
     */
    async _fetchPartialOrders() {
        try {
            const screenState = this.pos.ticketScreenState;
            const domain = this._computePartialOrdersDomain();
            const domainKey = JSON.stringify(domain);
            const offset = screenState.offsetByDomain[domainKey] || 0;
            const config_id = this.pos.config.id;

            const result = await this.pos.data.call(
                "pos.order",
                "search_partial_order_ids",
                [],
                { config_id, domain, limit: 30, offset }
            );

            const ordersInfo = Array.isArray(result) ? result[0] : result?.ordersInfo || [];
            const totalCount = Array.isArray(result) ? result[1] : result?.totalCount || 0;

            if (!screenState.offsetByDomain[domainKey]) {
                screenState.offsetByDomain[domainKey] = 0;
            }
            screenState.offsetByDomain[domainKey] += ordersInfo.length || 0;

            // Find missing or outdated orders
            const idsToFetch = ordersInfo
                .filter(([id, write_date]) => {
                    const cachedOrder = this.pos.models["pos.order"].get(id);
                    if (!cachedOrder) return true;
                    if (write_date && parseUTCString(write_date) > parseUTCString(cachedOrder.date_order)) {
                        return true;
                    }
                    return false;
                })
                .map(([id]) => id);

            if (idsToFetch.length > 0) {
                await this.pos.data.read("pos.order", Array.from(new Set(idsToFetch)));
            }

            // Collect orders from cache
            const loadedOrders = ordersInfo
                .map(([id]) => this.pos.models["pos.order"].get(id))
                .filter((o) => o);

            // Update persistent cache
            const cache = this._state.partialOrdersCache;
            loadedOrders.forEach((order) => {
                cache.cache[order.id] = order;
                if (!cache.orders.find((o) => o.id === order.id)) {
                    cache.orders.push(order);
                }
            });
            cache.totalCount = totalCount;

            this._applyPartialOrdersFromCache();
            this.render();

        } catch (error) {
            console.error("Error fetching partial orders:", error);
            this._applyPartialOrdersFromCache();
            this.render();
        }
    },

    /**
     * Sync cached partial orders to the UI state.
     */
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

    /**
     * Load more partial orders for pagination.
     */
    async _loadMorePartialOrders() {
        await this._fetchPartialOrders();
    },

    /**
     * @override
     * Calculate total for partial orders.
     */
    getTotal(order) {
        if (this._state.ui?.filter === "PARTIAL" && order) {
            return typeof order.get_total_with_tax === "function"
                ? order.get_total_with_tax()
                : order.amount_total || 0;
        }
        return super.getTotal(order);
    },

    /**
     * @override
     * Return the filtered list of orders, including partial ones.
     */
    getFilteredOrderList() {
        if (this._state.ui?.filter === "PARTIAL") {
            const orders = this._state.syncedOrders?.toShow || [];
            return orders;
        }
        return super.getFilteredOrderList();
    },

    /**
     * @override
     * Return the currently selected order.
     */
    getSelectedSyncedOrder() {
        if (this._state.ui?.filter === "PARTIAL") {
            const selectedId = this._state.selectedSyncedOrderId;
            const order = this._state.syncedOrders.cache[selectedId];
            return order || null;
        }
        return super.getSelectedSyncedOrder();
    },

    /**
     * @override
     * Determine if the delete button should be hidden (hidden for partial orders).
     */
    shouldHideDeleteButton(order) {
        if (this._state.ui?.filter === "PARTIAL") {
            return true;
        }
        return super.shouldHideDeleteButton(order);
    },

    /**
     * @override
     * Prevent deletion of partial orders from this screen.
     */
    _canDeleteOrder(order) {
        if (this._state.ui?.filter === "PARTIAL") {
            return false;
        }
        return super._canDeleteOrder(order);
    },

    /**
     * @override
     * Handle pagination.
     */
    async onNextPage() {
        if (this._state.ui?.filter === "PARTIAL") {
            await this._loadMorePartialOrders();
        } else {
            await super.onNextPage();
        }
    },
});
