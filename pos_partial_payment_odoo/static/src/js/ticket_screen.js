/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { deserializeDateTime, formatDateTime } from "@web/core/l10n/dates";
import { Order } from "@point_of_sale/app/store/models";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

const { DateTime } = luxon;

patch(TicketScreen.prototype, {
    //Create a new filter in POS FRONT END
    _getFilterOptions() {
        const orderStates = this._getOrderStates();
        orderStates.set('SYNCED', { text: _t('Paid') });
        orderStates.set('PARTIAL', { text: _t('Partial') });
        return orderStates;
    },
    //When Selecting Partial Payment Filter Function Works
    async onFilterSelected(selectedFilter) {
        this._state.ui.filter = selectedFilter;
        if (this._state.ui.filter == 'PARTIAL') {
            await this._fetchPartialOrders();
        }
        else {
            super.onFilterSelected(selectedFilter);
        }
    },
    //Search Function Overriding to add functionality Partial
    async _onSearch(event) {
        Object.assign(this._state.ui.searchDetails, event.detail);
        if (this._state.ui.filter == 'SYNCED') {
            this._state.syncedOrders.currentPage = 1;
            await this._fetchSyncedOrders();
        }
        if (this._state.ui.filter == 'PARTIAL') {
            this._state.syncedOrders.currentPage = 1;
            await this._fetchPartialOrders();
    }
    },
    //Fetching Partial Orders
    async _fetchPartialOrders() {
        const domain = this._computeSyncedOrdersDomain();
        const limit = this._state.syncedOrders.nPerPage;
        const offset =
                (this._state.syncedOrders.currentPage - 1) * this._state.syncedOrders.nPerPage;
        const config_id = this.pos.config.id;
        const { ids, totalCount } = await this.orm.call(
            "pos.order",
            "search_partial_order_ids",
            [],
            { config_id, domain, limit, offset }
        );
        const idsNotInCache = ids.filter((id) => !(id in this._state.syncedOrders.cache));
        const cacheDate = this._state.syncedOrders.cacheDate || DateTime.fromMillis(0);
        const idsNotUpToDate = ids.filter((orderInfo) => {
            return deserializeDateTime(orderInfo[1]) > cacheDate;
        });
        const idsToLoad = idsNotInCache.concat(idsNotUpToDate).map((info) => info[0]);
        if (idsNotInCache.length > 0) {
            const fetchedOrders = await this.orm.call("pos.order", "export_for_ui", [idsNotInCache]);
            // Check for missing products and partners and load them in the PoS
            await this.pos._loadMissingProducts(fetchedOrders);
            await this.pos._loadMissingPartners(fetchedOrders);
            // Cache these fetched orders so that next time, no need to fetch
            // them again, unless invalidated. See `_onInvoiceOrder`.
            fetchedOrders.forEach((order) => {
                this._state.syncedOrders.cache[order.id] = new Order(
                    { env: this.env },
                    { pos: this.pos, json: order }
                );
            });
        }
        this._state.syncedOrders.totalCount = totalCount;
        this._state.syncedOrders.toShow = ids.map((id) => this._state.syncedOrders.cache[id]);
    },
    //Adding Functionality POS FILTER to Show in POS FRONTEND
    getFilteredOrderList() {
        if (this._state.ui.filter == 'PARTIAL') return this._state.syncedOrders.toShow
        return super.getFilteredOrderList();
    },
    //Adding Functionality on Selecting Partial Order to be shown on POS FRONTEND
    getSelectedSyncedOrder() {
        if (this._state.ui.filter == 'PARTIAL') {
            return this._state.syncedOrders.cache[this._state.ui.selectedSyncedOrderId];
        }else{
        return super.getSelectedSyncedOrder();
        }
    }
})
