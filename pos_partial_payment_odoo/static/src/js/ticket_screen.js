/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
const { Order } = require('point_of_sale.models');
import TicketScreen from 'point_of_sale.TicketScreen';
const models = require('point_of_sale.models');

patch(TicketScreen.prototype, 'TicketScreen', {
    //Create a new filter in POS FRONT END
    _getFilterOptions() {
        const orderStates = this._getOrderStates();
        orderStates.set('SYNCED', {
            text: this.env._t('Paid')
        });
        orderStates.set('PARTIAL', {
            text: this.env._t('Partial')
        });
        return orderStates;
    },
    //When Selecting Partial Payment Filter Function Works
    async _onFilterSelected(event) {
        this._state.ui.filter = event.detail.filter;
        if (this._state.ui.filter == 'SYNCED') {
            await this._fetchSyncedOrders();
        }
        if (this._state.ui.filter == 'PARTIAL') {
            await this._fetchPartialOrders();
        }
            this.render();
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
        const offset = (this._state.syncedOrders.currentPage - 1) * this._state.syncedOrders.nPerPage;
        const { ids, totalCount} = await this.rpc({
            model: 'pos.order',
            method: 'search_partial_order_ids',
            kwargs: {
                config_id: this.env.pos.config.id,
                domain,
                limit,
                offset
            },
            context: this.env.session.user_context,
        });
        const idsNotInCache = ids.filter((id) => !(id in this._state.syncedOrders.cache));
        if (idsNotInCache.length > 0) {
            const fetchedOrders = await this.rpc({
                model: 'pos.order',
                method: 'export_for_ui',
                args: [idsNotInCache],
                context: this.env.session.user_context,
            });
            // Check for missing products and partners and load them in the PoS
            await this.env.pos._loadMissingProducts(fetchedOrders);
            await this.env.pos._loadMissingPartners(fetchedOrders);
            // Cache these fetched orders so that next time, no need to fetch
            // them again, unless invalidated. See `_onInvoiceOrder`.
            fetchedOrders.forEach((order) => {
                this._state.syncedOrders.cache[order.id] = new models.Order({}, { pos: this.env.pos, json: order });
            });
        }
        this._state.syncedOrders.totalCount = totalCount;
        this._state.syncedOrders.toShow = ids.map((id) => this._state.syncedOrders.cache[id]);
    },
    //Adding Functionality POS FILTER to Show in POS FRONTEND
    getFilteredOrderList() {
        if (this._state.ui.filter == 'PARTIAL') return this._state.syncedOrders.toShow;
        return this._super(...arguments);
    },
    //Adding Functionality on Selecting Partial Order to be shown on POS FRONTEND
    getSelectedSyncedOrder() {
        if (this._state.ui.filter == 'PARTIAL') {
            return this._state.syncedOrders.cache[this._state.ui.selectedSyncedOrderId];
        }
        return this._super(...arguments);
    }
})
