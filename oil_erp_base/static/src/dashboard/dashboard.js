/** @odoo-module **/
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";

export class OilDashboard extends Component {
    static template = "oil_erp_base.OilDashboard";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    setup() {
        this.action = useService("action");
        this.state = useState({
            brentPrice: null,
            brentDate: "",
            brentSource: "",
            wtiPrice: null,
            wtiDate: "",
            wtiSource: "",
            naturalGasPrice: null,
            naturalGasDate: "",
            naturalGasSource: "",
            henryHubPrice: null,
            henryHubDate: "",
            henryHubSource: "",
            commodityData: [],
            newsArticles: [],
            searchQuery: "",
            isLoading: true,
            lastRefresh: "",
            canConfigure: false,
        });

        this._refreshTimer = null;

        onWillStart(async () => {
            this.state.canConfigure = await this._canAccessConfiguration();
            await this._fetchAllData();
        });

        onMounted(() => {
            // Auto-refresh every 30 minutes
            this._refreshTimer = setInterval(() => this._fetchAllData(), 30 * 60 * 1000);
        });

        onWillUnmount(() => {
            if (this._refreshTimer) {
                clearInterval(this._refreshTimer);
            }
        });
    }

    async _oilPriceBatchFetch(codes) {
        return await rpc("/oil_erp/oil_price_batch", { codes });
    }

    async _newsFetch(endpoint, params) {
        return await rpc("/oil_erp/news_proxy", { endpoint, params });
    }

    async _canAccessConfiguration() {
        const [isOilManager, isOilAdmin, isSystemAdmin] = await Promise.all([
            user.hasGroup("oil_erp_base.group_oil_manager"),
            user.hasGroup("oil_erp_base.group_oil_admin"),
            user.hasGroup("base.group_system"),
        ]);
        return isOilManager || isOilAdmin || isSystemAdmin;
    }

    async _fetchAllData() {
        this.state.isLoading = true;
        try {
            await Promise.allSettled([
                this._fetchLiveOilMarketData(),
                this._fetchLiveNews(),
            ]);
            this.state.lastRefresh = new Date().toLocaleTimeString();
        } catch (err) {
            console.error("Dashboard fetch error:", err);
        } finally {
            this.state.isLoading = false;
        }
    }

    _formatDateTime(value) {
        if (!value) {
            return "";
        }
        const parsed = new Date(value);
        if (Number.isNaN(parsed.getTime())) {
            return value;
        }
        return parsed.toLocaleString();
    }

    async _fetchLiveOilMarketData() {
        const commodities = [
            { code: "NATURAL_GAS_USD", label: "Natural Gas" },
            { code: "NATURAL_GAS_USD", label: "Henry Hub Gas" },
            { code: "GASOLINE_USD", label: "Petrol" },
            { code: "GASOLINE_USD", label: "Gasoline" },
            { code: "DIESEL_USD", label: "Diesel" },
            { code: "DIESEL_USD", label: "ULSD Diesel" },
            { code: "HEATING_OIL_USD", label: "Heating Oil" },
            { code: "HEATING_OIL_USD", label: "No. 2 Heating Oil" },
            { code: "JET_FUEL_USD", label: "Jet Fuel" },
            { code: "JET_FUEL_USD", label: "Aviation Fuel" },
            { code: "WTI_USD", label: "WTI Crude", card: "wti" },
            { code: "BRENT_CRUDE_USD", label: "Brent Crude", card: "brent" },
            { code: "GASOLINE_USD", label: "Motor Fuel" },
            { code: "DIESEL_USD", label: "Transport Diesel" },
            { code: "HEATING_OIL_USD", label: "Industrial Heating Oil" },
        ];
        try {
            const payload = await this._oilPriceBatchFetch(commodities.map((item) => item.code));
            const rows = [];
            commodities.forEach((item, index) => {
                const result = payload?.[item.code];
                const data = result?.data;
                const price = parseFloat(data?.price);
                if (Number.isNaN(price)) {
                    return;
                }
                const formattedDate = this._formatDateTime(data?.created_at);
                if (item.card === "brent") {
                    this.state.brentPrice = price.toFixed(2);
                    this.state.brentDate = formattedDate;
                    this.state.brentSource = "Global Market Feed";
                } else if (item.card === "wti") {
                    this.state.wtiPrice = price.toFixed(2);
                    this.state.wtiDate = formattedDate;
                    this.state.wtiSource = "Global Market Feed";
                } else if (item.label === "Natural Gas") {
                    this.state.naturalGasPrice = price.toFixed(4);
                    this.state.naturalGasDate = formattedDate;
                    this.state.naturalGasSource = "Global Market Feed";
                } else if (item.label === "Henry Hub Gas") {
                    this.state.henryHubPrice = price.toFixed(4);
                    this.state.henryHubDate = formattedDate;
                    this.state.henryHubSource = "Global Market Feed";
                }
                rows.push({
                    id: `${item.code}_${index}`,
                    commodity: item.label,
                    code: item.code,
                    value: price.toFixed(price < 10 ? 4 : 2),
                    period: formattedDate,
                    source: "Global Market Feed",
                    unit: "USD",
                });
            });
            const filteredRows = rows.filter((item) => !["WTI Crude", "Brent Crude"].includes(item.commodity));
            const maxVal = filteredRows.length
                ? Math.max(...filteredRows.map((item) => parseFloat(item.value) || 0))
                : 1;
            for (const item of filteredRows) {
                item.pct = ((parseFloat(item.value) / maxVal) * 100).toFixed(0);
            }
            filteredRows.sort((a, b) => a.commodity.localeCompare(b.commodity));
            this.state.commodityData = filteredRows;
        } catch (e) {
            console.error("Commodity overview fetch failed:", e);
            this.state.commodityData = [];
        }
    }

    async _fetchLiveNews() {
        try {
            const json = await this._newsFetch("search", {});
            const articles = Array.isArray(json?.articles) ? json.articles : [];
            this.state.newsArticles = articles.map((article, index) => ({
                id: article.url || index,
                title: article.title || "Untitled article",
                description: article.description || "",
                source: article.source?.name || "Unknown source",
                publishedAt: article.publishedAt || "",
                url: article.url || "#",
            }));
        } catch (e) {
            console.error("Live news fetch failed:", e);
            this.state.newsArticles = [];
        }
    }

    get filteredCommodityData() {
        const query = (this.state.searchQuery || "").toLowerCase().trim();
        if (!query) {
            return this.state.commodityData;
        }
        return this.state.commodityData.filter((item) =>
            item.commodity.toLowerCase().includes(query) ||
            item.code.toLowerCase().includes(query)
        );
    }

    get hasNewsArticles() {
        return this.state.newsArticles.length > 0;
    }

    get hasMarketData() {
        return Boolean(
            this.state.brentPrice ||
            this.state.wtiPrice ||
            this.state.naturalGasPrice ||
            this.state.henryHubPrice ||
            this.state.commodityData.length
        );
    }

    get showCombinedEmptyState() {
        return !this.hasMarketData && !this.hasNewsArticles;
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    async onRefresh() {
        await this._fetchAllData();
    }

    async onConfigure() {
        await this.action.doAction("oil_erp_base.action_oil_config_settings");
        this._scrollToIntegration();
    }

    _scrollToIntegration(attempt = 0) {
        const targetEl = document.querySelector("#oil_news_integration_setting")
            || document.querySelector("#oil_live_price_integration_setting");
        if (targetEl) {
            targetEl.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });
            return;
        }
        if (attempt < 12) {
            setTimeout(() => this._scrollToIntegration(attempt + 1), 250);
        }
    }
}

registry.category("actions").add("oil_base.dashboard", OilDashboard);
