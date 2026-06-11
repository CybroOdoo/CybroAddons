/** @odoo-module */

import { Component, useRef, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

class ProductExpiryDashboard extends Component {

    static template = "odoo_product_expiry_dashboard.expiry_dashboard_template";

    setup() {

        /* ---- Services ---- */
        this.actionService = useService("action");

        /* ---- State ---- */
        this.state = useState({
            startDate: null,
            endDate: null,
            expire_quantity: {},
        });

        /* ---- Refs ---- */
        this.rootRef = useRef("root");

        this.expiredRef = useRef("expiredProducts");
        this.expiredCatRef = useRef("expiredCategory");

        this.nearWarehouseRef = useRef("nearWarehouse");
        this.nearLocationRef = useRef("nearLocation");
        this.nearProductRef = useRef("nearProduct");
        this.nearCategoryRef = useRef("nearCategory");


        this.emptyRefs = {
            expired: useRef("expiredProductsEmpty"),
            expiredCat: useRef("expiredCategoryEmpty"),
            nearProd: useRef("nearProductEmpty"),
            nearCat: useRef("nearCategoryEmpty"),
            nearLoc: useRef("nearLocationEmpty"),
            nearWh: useRef("nearWarehouseEmpty"),
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

    FilterDate = async () => {

        if (!this.rootRef.el) return;

        this.state.startDate = this.rootRef.el.querySelector("#start_date")?.value || null;
        this.state.endDate = this.rootRef.el.querySelector("#end_date")?.value || null;

        this.destroyCharts();
        await this.loadDashboard();
    };

    /* -------------------- TILES -------------------- */

    async loadTiles() {

        const result = await rpc('/web/dataset/call_kw/stock.lot/get_product_expiry', {
            model: 'stock.lot',
            method: 'get_product_expiry',
            args: [this.datePayload],
            kwargs: {},
        });

        this.state.expire_quantity = result || {};
        console.log("EXPIRY RAW DATA", this.state.expire_quantity);

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


        if (!labels.length || !ref.el) {
            if (emptyRef?.el) emptyRef.el.style.display = "";
            return;
        }

        if (emptyRef?.el) emptyRef.el.style.display = "none";

        this.charts[key]?.destroy();

        this.charts[key] = new Chart(ref.el, {
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

    /* -------------------- EXPIRED CHARTS -------------------- */

    async loadExpiredProducts() {

        const data = await rpc('/web/dataset/call_kw/stock.lot/get_expired_product', {
            model: 'stock.lot',
            method: 'get_expired_product',
            args: [this.datePayload],
            kwargs: {},
        });

        this.renderChart(data, this.expiredRef, "expired", "pie");
    }

    async loadExpiredByCategory() {

        const data = await rpc('/web/dataset/call_kw/stock.lot/get_product_expiry_by_category', {
            model: 'stock.lot',
            method: 'get_product_expiry_by_category',
            args: [this.datePayload],
            kwargs: {},
        });
        console.log(data, 'daata')

        this.renderChart(data, this.expiredCatRef, "expiredCat", "bar");
    }

    /* -------------------- NEAR EXPIRY CHARTS -------------------- */

    async loadNearWarehouse() {
        const data = await rpc('/web/dataset/call_kw/stock.lot/get_expire_product_warehouse', {
            model: 'stock.lot',
            method: 'get_expire_product_warehouse',
            args: [],
            kwargs: {},
        });

        this.renderChart(data, this.nearWarehouseRef, "nearWh", "doughnut");
    }

    async loadNearLocation() {
        const data = await rpc('/web/dataset/call_kw/stock.lot/get_expire_product_location', {
            model: 'stock.lot',
            method: 'get_expire_product_location',
            args: [],
            kwargs: {},
        });

        this.renderChart(data, this.nearLocationRef, "nearLoc", "pie");
    }

    async loadNearProduct() {
        const data = await rpc('/web/dataset/call_kw/stock.lot/get_near_expiry_product', {
            model: 'stock.lot',
            method: 'get_near_expiry_product',
            args: [],
            kwargs: {},
        });

        this.renderChart(data, this.nearProductRef, "nearProd", "doughnut");
    }

    async loadNearCategory() {
        const data = await rpc('/web/dataset/call_kw/stock.lot/get_near_expiry_category', {
            model: 'stock.lot',
            method: 'get_near_expiry_category',
            args: [],
            kwargs: {},
        });

        this.renderChart(data, this.nearCategoryRef, "nearCat", "line");
    }

    /* -------------------- TILE ACTIONS -------------------- */

    expired_click = () => this.navigate(-1, "Expired");
    today_click = () => this.navigate(0, "Expire Today");
    one_day_click = () => this.navigate(1, "Expiry in One Day");
    seven_day_click = () => this.navigate(7, "Expiry in Seven Days");
    thirty_day_click = () => this.navigate(30, "Expiry in Thirty Days");
    one_twenty_day_click = () => this.navigate(120, "Expiry in One Twenty Days");

    navigate(days, name) {
        console.log(days, name, 'DDD')

        const Domain = [];

        if (this.state.startDate)
            Domain.push(["expiration_date", ">=", this.state.startDate]);

        if (this.state.endDate)
            Domain.push(["expiration_date", "<=", this.state.endDate]);

        const today = new Date();
        today.setHours(0,0,0,0);

        if (days === -1) {
            Domain.push(["expiration_date", "<", today]);
        }
        else if (days === 0) {
            const tomorrow = new Date(today);
            tomorrow.setDate(tomorrow.getDate() + 1);
            Domain.push(["expiration_date", ">=", today]);
            Domain.push(["expiration_date", "<", tomorrow]);
        }
        else {
            const from = new Date(today);
            from.setDate(from.getDate() + 1);

            const to = new Date(today);
//            to.setDate(to.getDate() + days);
            to.setDate(today.getDate() + days + 1);
            console.log(from, to, 'from to')

            Domain.push(["expiration_date", ">=", from]);
            Domain.push(["expiration_date", "<=", to]);
        }
        console.log(Domain, 'Domain')

            this.actionService.doAction({
            name,
            type: "ir.actions.act_window",
            view_mode: "list",
            res_model: "stock.lot",
            views: [[false, "list"], [false, "form"]],
            domain: Domain,
        });
    }
}

registry.category("actions").add("product_expiry", ProductExpiryDashboard);
