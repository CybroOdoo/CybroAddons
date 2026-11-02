/** @odoo-module */

import { Component, signal, proxy, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";

function makeRef() {
    const r = signal.ref();
    Object.defineProperty(r, "el", {
        get() {
            return r();
        },
    });
    return r;
}

class ProductExpiryDashboard extends Component {

    static template = "odoo_product_expiry_dashboard.expiry_dashboard_template";

    setup() {

        /* ---- Services ---- */
        this.actionService = useService("action");
        this.orm = useService("orm");

        /* ---- State ---- */
        this.state = proxy({
            startDate: null,
            endDate: null,
            expire_quantity: {},
        });

        onWillStart(() => loadBundle("web.chartjs_lib"));

        /* ---- Refs ---- */
        this.root = makeRef();
        this.rootRef = this.root;

        this.expiredProducts = makeRef();
        this.expiredRef = this.expiredProducts;
        this.expiredProductsEmpty = makeRef();

        this.expiredCategory = makeRef();
        this.expiredCatRef = this.expiredCategory;
        this.expiredCategoryEmpty = makeRef();

        this.nearProduct = makeRef();
        this.nearProductRef = this.nearProduct;
        this.nearProductEmpty = makeRef();

        this.nearCategory = makeRef();
        this.nearCategoryRef = this.nearCategory;
        this.nearCategoryEmpty = makeRef();

        this.nearLocation = makeRef();
        this.nearLocationRef = this.nearLocation;
        this.nearLocationEmpty = makeRef();

        this.nearWarehouse = makeRef();
        this.nearWarehouseRef = this.nearWarehouse;
        this.nearWarehouseEmpty = makeRef();

        this.emptyRefs = {
            expired: this.expiredProductsEmpty,
            expiredCat: this.expiredCategoryEmpty,
            nearProd: this.nearProductEmpty,
            nearCat: this.nearCategoryEmpty,
            nearLoc: this.nearLocationEmpty,
            nearWh: this.nearWarehouseEmpty,
        };

        /* ---- Chart registry ---- */
        this.charts = {};

        onMounted(() => this.loadDashboard());
        onWillUnmount(() => this.destroyCharts());
    }

    /* -------------------- Utilities -------------------- */

    get datePayload() {
        return {
            start_date: this.state.startDate,
            end_date: this.state.endDate,
        };
    }

    destroyCharts() {
        Object.values(this.charts).forEach(c => c?.destroy());
        this.charts = {};
    }

    /* -------------------- Initial Load -------------------- */

    async loadDashboard() {
        await this.loadTiles();
        await this.loadAllCharts();
    }

    async loadAllCharts() {
        await Promise.all([
            this.loadExpiredProducts(),
            this.loadExpiredByCategory(),
            this.loadNearWarehouse(),
            this.loadNearLocation(),
            this.loadNearProduct(),
            this.loadNearCategory(),
        ]);
    }

    /* -------------------- DATE CHANGE HANDLER -------------------- */

    filterDate = async () => {
        const rootEl = this.rootRef.el || (typeof this.rootRef === "function" ? this.rootRef() : null);
        if (!rootEl) return;

        this.state.startDate = rootEl.querySelector("#start_date")?.value || null;
        this.state.endDate = rootEl.querySelector("#end_date")?.value || null;

        this.destroyCharts();
        await this.loadDashboard();
    };

    /* -------------------- TILES -------------------- */

    async loadTiles() {
        const result = await this.orm.call("stock.lot", "get_product_expiry", [this.datePayload]);
        this.state.expire_quantity = result || {};
    }

    /* -------------------- GENERIC CHART -------------------- */

    renderChart(data, ref, key, type) {
        const labels = [];
        const values = [];

        for (const [k, v] of Object.entries(data || {})) {
            labels.push(k);
            values.push(v);
        }

        const emptyRef = this.emptyRefs[key];
        const canvasEl = ref?.el || (typeof ref === "function" ? ref() : null);
        const emptyEl = emptyRef?.el || (typeof emptyRef === "function" ? emptyRef() : null);

        if (!labels.length || !canvasEl) {
            if (emptyEl) emptyEl.style.display = "";
            if (canvasEl) canvasEl.style.display = "none";
            return;
        }

        if (emptyEl) emptyEl.style.display = "none";
        if (canvasEl) canvasEl.style.display = "";

        this.charts[key]?.destroy();

        if (typeof Chart !== "undefined") {
            this.charts[key] = new Chart(canvasEl, {
                type,
                data: {
                    labels,
                    datasets: [{
                        label: "Quantity",
                        data: values,
                        borderWidth: 1,
                    }]
                }
            });
        }
    }

    /* -------------------- EXPIRED CHARTS -------------------- */

    async loadExpiredProducts() {
        const data = await this.orm.call("stock.lot", "get_expired_product", [this.datePayload]);
        this.renderChart(data, this.expiredRef, "expired", "pie");
    }

    async loadExpiredByCategory() {
        const data = await this.orm.call("stock.lot", "get_product_expiry_by_category", [this.datePayload]);
        this.renderChart(data, this.expiredCatRef, "expiredCat", "bar");
    }

    /* -------------------- NEAR EXPIRY CHARTS -------------------- */

    async loadNearWarehouse() {
        const data = await this.orm.call("stock.lot", "get_expire_product_warehouse", []);
        this.renderChart(data, this.nearWarehouseRef, "nearWh", "doughnut");
    }

    async loadNearLocation() {
        const data = await this.orm.call("stock.lot", "get_expire_product_location", []);
        this.renderChart(data, this.nearLocationRef, "nearLoc", "pie");
    }

    async loadNearProduct() {
        const data = await this.orm.call("stock.lot", "get_near_expiry_product", []);
        this.renderChart(data, this.nearProductRef, "nearProd", "doughnut");
    }

    async loadNearCategory() {
        const data = await this.orm.call("stock.lot", "get_near_expiry_category", []);
        this.renderChart(data, this.nearCategoryRef, "nearCat", "line");
    }

    /* -------------------- TILE ACTIONS -------------------- */

    expired_click = () => this.navigate(-1, "Expired");
    today_click = () => this.navigate(0, "Expire Today");
    one_day_click = () => this.navigate(1, "Expiry in One Day");
    seven_day_click = () => this.navigate(7, "Expiry in Seven Days");
    thirty_day_click = () => this.navigate(30, "Expiry in Thirty Days");
    one_twenty_day_click = () => this.navigate(120, "Expiry in 120 Days");

    navigate(days, name) {
        const domain = [];

        // Exclude zero-quantity lots to match the tile counts
        domain.push(["product_qty", ">", 0]);

        if (this.state.startDate) {
            domain.push(["expiration_date", ">=", this.state.startDate]);
        }

        if (this.state.endDate) {
            domain.push(["expiration_date", "<=", this.state.endDate + " 23:59:59"]);
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const formatDateStr = (d) => {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, "0");
            const day = String(d.getDate()).padStart(2, "0");
            return `${year}-${month}-${day}`;
        };

        if (days === -1) {
            domain.push(["expiration_date", "<", formatDateStr(today)]);
        } else if (days === 0) {
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            domain.push(["expiration_date", ">=", formatDateStr(today)]);
            domain.push(["expiration_date", "<", formatDateStr(tomorrow)]);
        } else {
            const from = new Date(today);
            from.setDate(from.getDate() + 1);

            const to = new Date(today);
            to.setDate(today.getDate() + days);

            domain.push(["expiration_date", ">=", formatDateStr(from)]);
            domain.push(["expiration_date", "<=", formatDateStr(to) + " 23:59:59"]);
        }

        this.actionService.doAction({
            name,
            type: "ir.actions.act_window",
            view_mode: "list",
            res_model: "stock.lot",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }
}

registry.category("actions").add("product_expiry", ProductExpiryDashboard);
