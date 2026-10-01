/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { Component, onMounted, onWillUnmount, proxy, onWillStart } from "@odoo/owl";

/**
 * IT Hardware Dashboard — Compact Component (Odoo saas-19.4)
 * Real-time executive management dashboard with KPI cards, Chart.js analytics,
 * date filter controls, and operational audit tables.
 */
export class ITHardwareDashboard extends Component {
    static template = "it_hardware_saas.ITHardwareDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.charts = {};

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        // OWL v3 reactive state configuration
        this.state = proxy({
            loading: true,
            isDarkMode: false,
            showAdvancedFilters: false,
            today: this._formatDateDisplay(new Date()),
            lastRefreshed: "",
            // Filter Bar State
            filters: {
                dateStart: "",
                dateEnd: "",
            },
            attendanceDashArray: "0 110",
            kpi: {
                activeCustomers: 0,
                mrr: "$0",
                activeTickets: 0,
                totalSales: "$0",
                pendingQuotes: "$0",
                avgOrderValue: "$0",
                underRepair: 0,
                sessionsToday: 0,
                slaRate: "0%",
                technicianUtilization: "0%",
            },
            recentOrders: [],
            todaySchedule: [],
            technicianAvailability: [],
            // Insights Panel
            insights: {
                topTechnician: "—",
                topTechnicianId: false,
                highestCategory: "—",
                renewalRate: "0%",
                equipUtilization: "0%",
            },
            // Charts Data
            chartsData: {
                categoryPopularity: [],
                revenueTrend: [],
                technicianWorkload: [],
                serviceTypeBreakdown: [],
                repairCostBreakdown: [],
                customerSLADistribution: [],
            }
        });

        // Auto Refresh Interval Setup (Every 30 seconds)
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData(true); // silent refresh
        }, 30000);

        onMounted(() => {
            this.loadDashboardData();

            // Observe Odoo Theme Radio changes dynamically
            if (typeof MutationObserver !== "undefined") {
                this.themeObserver = new MutationObserver(() => {
                    this._initCharts();
                });
                const obsConfig = { attributes: true, attributeFilter: ["data-bs-theme", "data-color-mode", "data-color-scheme", "class"] };
                if (document.documentElement) {
                    this.themeObserver.observe(document.documentElement, obsConfig);
                }
                if (document.body) {
                    this.themeObserver.observe(document.body, obsConfig);
                }
            }
        });

        onWillUnmount(() => {
            this._destroyCharts();
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            if (this.themeObserver) {
                this.themeObserver.disconnect();
            }
        });
    }

    _destroyCharts() {
        Object.values(this.charts).forEach((chart) => {
            if (chart) {
                try { chart.destroy(); } catch (_) { }
            }
        });
        this.charts = {};
    }

    toggleAdvancedFilters() {
        this.state.showAdvancedFilters = !this.state.showAdvancedFilters;
    }

    onFilterChange(name, ev) {
        const val = ev.target.value;
        this.state.filters[name] = val;
        this.loadDashboardData(true);
    }

    clearFilters() {
        this.state.filters.dateStart = "";
        this.state.filters.dateEnd = "";
        const inputs = document.querySelectorAll(".header_filter_input, .filter_input");
        inputs.forEach(i => i.value = "");
        this.loadDashboardData(true);
    }

    // Filter Domain Builders
    _getSalesDomain(baseDomain = []) {
        const domain = [...baseDomain];
        if (this.state.filters.dateStart) {
            domain.push(["date_order", ">=", this.state.filters.dateStart + " 00:00:00"]);
        }
        if (this.state.filters.dateEnd) {
            domain.push(["date_order", "<=", this.state.filters.dateEnd + " 23:59:59"]);
        }
        return domain;
    }

    _getTicketsDomain(baseDomain = []) {
        const domain = [...baseDomain];
        if (this.state.filters.dateStart) {
            domain.push(["create_date", ">=", this.state.filters.dateStart + " 00:00:00"]);
        }
        if (this.state.filters.dateEnd) {
            domain.push(["create_date", "<=", this.state.filters.dateEnd + " 23:59:59"]);
        }
        return domain;
    }

    _getTasksDomain(baseDomain = []) {
        const domain = [...baseDomain];
        if (this.state.filters.dateStart) {
            domain.push(["x_visit_date", ">=", this.state.filters.dateStart]);
        }
        if (this.state.filters.dateEnd) {
            domain.push(["x_visit_date", "<=", this.state.filters.dateEnd]);
        }
        return domain;
    }

    _getRepairsDomain(baseDomain = []) {
        const domain = [...baseDomain];
        if (this.state.filters.dateStart) {
            domain.push(["create_date", ">=", this.state.filters.dateStart + " 00:00:00"]);
        }
        if (this.state.filters.dateEnd) {
            domain.push(["create_date", "<=", this.state.filters.dateEnd + " 23:59:59"]);
        }
        return domain;
    }



    async loadDashboardData(silent = false) {
        if (!silent) {
            this.state.loading = true;
        }
        try {
            await Promise.all([
                this._loadKPIs(),
                this._loadRecentOrders(),
                this._loadTodaySchedule(),
                this._loadTechnicianAvailability(),
                this._loadChartsData(),
            ]);
            await this._loadAdvancedInsights();
            this.state.lastRefreshed = this._formatTimeDisplay(new Date());
        } catch (err) {
            console.error("[ITHardwareDashboard] Error loading data:", err);
        } finally {
            this.state.loading = false;
            setTimeout(() => this._initCharts(), 150);
        }
    }

    async _loadKPIs() {
        const [custCount, ticketCount, visitCount] =
            await Promise.all([
                this.orm.searchCount("res.partner", []),
                this.orm.searchCount("helpdesk.ticket", this._getTicketsDomain([])),
                this.orm.searchCount("project.task", this._getTasksDomain([])),
            ]);

        // Monthly Revenue (account.move)
        let monthlyRevenue = 0;
        try {
            const mrrDomainBase = [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "=", "paid"],
                ["invoice_date", "!=", false],
            ];
            if (this.state.filters.dateStart) {
                mrrDomainBase.push(["invoice_date", ">=", this.state.filters.dateStart]);
            }
            if (this.state.filters.dateEnd) {
                mrrDomainBase.push(["invoice_date", "<=", this.state.filters.dateEnd]);
            }

            const mrrInvoices = await this.orm.searchRead(
                "account.move",
                mrrDomainBase,
                ["amount_total"]
            );
            monthlyRevenue = mrrInvoices.reduce((sum, inv) => sum + inv.amount_total, 0);
        } catch (_) { }

        // Sales Revenue & Quotation Metrics (sale.order)
        let totalSalesVal = 0;
        let pendingQuotesVal = 0;
        let avgOrderVal = 0;
        let underRepairCount = 0;
        try {
            const confirmedOrders = await this.orm.searchRead(
                "sale.order",
                this._getSalesDomain([["state", "in", ["sale", "done"]]]),
                ["amount_total"]
            );
            totalSalesVal = confirmedOrders.reduce((sum, o) => sum + (o.amount_total || 0), 0);
            if (confirmedOrders.length > 0) {
                avgOrderVal = Math.round(totalSalesVal / confirmedOrders.length);
            }

            const draftQuotes = await this.orm.searchRead(
                "sale.order",
                this._getSalesDomain([["state", "in", ["draft", "sent"]]]),
                ["amount_total"]
            );
            pendingQuotesVal = draftQuotes.reduce((sum, o) => sum + (o.amount_total || 0), 0);

            underRepairCount = await this.orm.searchCount("repair.order", this._getRepairsDomain([["state", "not in", ["done", "cancel"]]]));
        } catch (_) { }

        // CRM Leads / Pipeline Revenue
        let crmLeadRev = 0;
        try {
            const leads = await this.orm.searchRead(
                "crm.lead",
                [["type", "=", "opportunity"], ["probability", "<", 100]],
                ["expected_revenue"]
            );
            crmLeadRev = leads.reduce((sum, l) => sum + (l.expected_revenue || 0), 0);
        } catch (_) { }

        this.state.kpi = proxy({
            activeCustomers: custCount || 0,
            mrr: this._formatCurrency(monthlyRevenue),
            totalSales: this._formatCurrency(totalSalesVal),
            crmPipeline: this._formatCurrency(crmLeadRev),
            pendingQuotes: this._formatCurrency(pendingQuotesVal),
            avgOrderValue: this._formatCurrency(avgOrderVal),
            underRepair: underRepairCount || 0,
            activeTickets: ticketCount || 0,
            sessionsToday: visitCount || 0,
            technicianUtilization: custCount > 0 ? "100%" : "0%",
        });
    }

    async _loadRecentOrders() {
        try {
            const records = await this.orm.searchRead(
                "sale.order",
                [],
                ["name", "partner_id", "amount_total", "state"],
                { limit: 5, order: "date_order desc, id desc" }
            );

            this.state.recentOrders = records.map((r) => {
                const partnerName = r.partner_id ? r.partner_id[1] : "Customer";
                let stateLabel = "Quotation";
                if (r.state === "sale") stateLabel = "Sales Order";
                else if (r.state === "done") stateLabel = "Locked";
                else if (r.state === "sent") stateLabel = "Quotation Sent";
                else if (r.state === "cancel") stateLabel = "Cancelled";

                return {
                    id: r.id,
                    name: r.name,
                    partner: partnerName,
                    amount: this._formatCurrency(r.amount_total || 0),
                    status: stateLabel,
                    state: r.state,
                };
            });
        } catch (_) {
            this.state.recentOrders = [];
        }
    }

    async _loadTodaySchedule() {
        try {
            const records = await this.orm.searchRead(
                "project.task",
                [],
                ["name", "x_partner_id", "x_technician_id", "x_service_type", "x_visit_date"],
                { limit: 5 }
            );
            this.state.todaySchedule = records.map((r) => ({
                id: r.id,
                time: r.x_visit_date ? new Date(r.x_visit_date).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }) : "Today",
                member: r.x_partner_id ? r.x_partner_id[1] : "—",
                trainer: r.x_technician_id ? r.x_technician_id[1] : "Unassigned",
                type: r.x_service_type || "Installation",
                status: "Scheduled",
            }));
        } catch (_) {
            this.state.todaySchedule = [];
        }
    }

    async _loadTechnicianAvailability() {
        try {
            const users = await this.orm.searchRead("res.users", [["share", "=", false]], ["id", "name"], { limit: 5 });
            this.state.technicianAvailability = users.map(u => ({
                id: u.id,
                name: u.name,
                jobTitle: "Field Technician",
                sessionsCount: 0,
                status: "Available",
            }));
        } catch (_) {
            this.state.technicianAvailability = [];
        }
    }

    async _loadChartsData() {
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const todayDate = new Date();
        const monthlyRevenueMap = {};
        for (let i = 5; i >= 0; i--) {
            const d = new Date(todayDate.getFullYear(), todayDate.getMonth() - i, 1);
            const key = `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
            monthlyRevenueMap[key] = { month: monthNames[d.getMonth()], label: monthNames[d.getMonth()], revenue: 0, sortKey: d.getTime() };
        }

        let totalRev = 0;
        try {
            const invoices = await this.orm.searchRead(
                "account.move",
                [["move_type", "=", "out_invoice"], ["state", "=", "posted"]],
                ["invoice_date", "amount_total"],
                { limit: 50 }
            );
            invoices.forEach(inv => {
                if (!inv.invoice_date) return;
                const invDate = new Date(inv.invoice_date);
                const key = `${monthNames[invDate.getMonth()]} ${invDate.getFullYear()}`;
                if (key in monthlyRevenueMap) {
                    monthlyRevenueMap[key].revenue += inv.amount_total;
                    totalRev += inv.amount_total;
                }
            });
        } catch (_) { }

        if (totalRev === 0) {
            try {
                const orders = await this.orm.searchRead(
                    "sale.order",
                    [],
                    ["date_order", "amount_total"],
                    { limit: 50 }
                );
                orders.forEach(so => {
                    if (!so.date_order) return;
                    const soDate = new Date(so.date_order);
                    const key = `${monthNames[soDate.getMonth()]} ${soDate.getFullYear()}`;
                    if (key in monthlyRevenueMap) {
                        monthlyRevenueMap[key].revenue += (so.amount_total || 0);
                        totalRev += (so.amount_total || 0);
                    }
                });
            } catch (_) { }
        }

        const revenueTrend = Object.keys(monthlyRevenueMap)
            .map(k => monthlyRevenueMap[k])
            .sort((a, b) => a.sortKey - b.sortKey);

        // 1. Service Type Breakdown Data
        let serviceTypeMap = { repair: 0, config: 0, troubleshoot: 0, installation: 0, preventive: 0 };
        try {
            const tickets = await this.orm.searchRead("helpdesk.ticket", [], ["x_service_type"]);
            tickets.forEach(t => {
                const st = t.x_service_type || "repair";
                if (st in serviceTypeMap) { serviceTypeMap[st] += 1; }
                else { serviceTypeMap[st] = 1; }
            });
        } catch (_) { }

        const serviceTypeBreakdown = [
            { label: "Hardware Repair", count: serviceTypeMap.repair || 0 },
            { label: "Configuration", count: serviceTypeMap.config || 0 },
            { label: "Troubleshooting", count: serviceTypeMap.troubleshoot || 0 },
            { label: "Installation", count: serviceTypeMap.installation || 0 },
            { label: "Preventive Maintenance", count: serviceTypeMap.preventive || 0 },
        ];

        // 2. Repair Cost Breakdown Data
        let repairCostData = [];
        try {
            const repairs = await this.orm.searchRead("repair.order", [], ["name", "x_labour_cost", "x_spare_parts_cost", "x_repair_cost"], { limit: 4 });
            repairCostData = repairs.map(r => ({
                job: r.name || "Repair Job",
                labour: r.x_labour_cost || 0,
                parts: r.x_spare_parts_cost || 0,
                total: r.x_repair_cost || 0,
            }));
        } catch (_) { }

        // 3. Customer SLA Distribution Data
        let slaMap = { platinum: 0, gold: 0, standard: 0, basic: 0 };
        try {
            const partners = await this.orm.searchRead("res.partner", [], ["x_service_level"]);
            partners.forEach(p => {
                const lvl = (p.x_service_level || "standard").toLowerCase();
                if (lvl in slaMap) { slaMap[lvl] += 1; }
                else { slaMap.standard += 1; }
            });
        } catch (_) { }

        const customerSLADistribution = [
            { tier: "Platinum SLA (24/7)", count: slaMap.platinum || 0 },
            { tier: "Gold SLA (Same Day)", count: slaMap.gold || 0 },
            { tier: "Standard SLA (48h)", count: slaMap.standard || 0 },
            { tier: "Basic SLA (Best Effort)", count: slaMap.basic || 0 },
        ];

        // Dynamic Technician Workload & Category Popularity
        let taskCompleted = 0, taskInProgress = 0, taskPending = 0;
        try {
            const tasks = await this.orm.searchRead("project.task", [], ["state"]);
            tasks.forEach(t => {
                if (t.state === "1_done" || t.state === "done") taskCompleted++;
                else if (t.state === "01_in_progress" || t.state === "in_progress") taskInProgress++;
                else taskPending++;
            });
        } catch (_) { }

        let categMap = {};
        try {
            const prods = await this.orm.searchRead("product.template", [], ["categ_id"]);
            prods.forEach(p => {
                const name = p.categ_id ? p.categ_id[1] : "General Hardware";
                categMap[name] = (categMap[name] || 0) + 1;
            });
        } catch (_) { }

        const categoryPopularity = Object.keys(categMap).map(k => ({ name: k, count: categMap[k] }));

        this.state.chartsData = proxy({
            revenueTrend,
            technicianWorkload: [
                { status: "Resolved", count: taskCompleted },
                { status: "In Progress", count: taskInProgress },
                { status: "Pending", count: taskPending },
            ],
            categoryPopularity: categoryPopularity.length > 0 ? categoryPopularity : [{ name: "Hardware", count: 0 }],
            serviceTypeBreakdown,
            repairCostBreakdown: repairCostData,
            customerSLADistribution,
        });
    }

    async _loadAdvancedInsights() {
        let topTech = "—";
        let topTechId = false;
        let topCateg = "—";

        try {
            const tasks = await this.orm.searchRead("project.task", [["user_ids", "!=", false]], ["user_ids"], { limit: 10 });
            if (tasks.length > 0 && tasks[0].user_ids.length > 0) {
                topTech = tasks[0].user_ids[0][1] || "—";
                topTechId = tasks[0].user_ids[0][0];
            }
        } catch (_) { }

        try {
            const prods = await this.orm.searchRead("product.template", [["categ_id", "!=", false]], ["categ_id"], { limit: 1 });
            if (prods.length > 0 && prods[0].categ_id) {
                topCateg = prods[0].categ_id[1];
            }
        } catch (_) { }

        this.state.insights = proxy({
            topTechnician: topTech,
            topTechnicianId: topTechId,
            highestCategory: topCateg,
            renewalRate: "0%",
            equipUtilization: "0%",
        });
    }

    toggleThemeMode() {
        const currentIsDark = this._isDarkMode();
        const nextMode = currentIsDark ? "light" : "dark";

        if (document.documentElement) {
            document.documentElement.setAttribute("data-bs-theme", nextMode);
            document.documentElement.setAttribute("data-color-mode", nextMode);
            document.documentElement.setAttribute("data-color-scheme", nextMode);
        }
        if (document.body) {
            document.body.setAttribute("data-bs-theme", nextMode);
            if (nextMode === "dark") {
                document.body.classList.add("o_dark_mode");
                document.body.classList.remove("o_light_mode");
            } else {
                document.body.classList.remove("o_dark_mode");
                document.body.classList.add("o_light_mode");
            }
        }

        this.state.isDarkMode = !currentIsDark;
        this._initCharts();
    }

    _isDarkMode() {
        const html = document.documentElement;
        const body = document.body;

        // 1. Check explicit Light Mode settings from Odoo Theme Switcher radio
        const htmlBsTheme = html ? html.getAttribute("data-bs-theme") : null;
        const htmlColorMode = html ? html.getAttribute("data-color-mode") : null;
        const htmlColorScheme = html ? html.getAttribute("data-color-scheme") : null;
        const bodyBsTheme = body ? body.getAttribute("data-bs-theme") : null;

        if (
            htmlBsTheme === "light" ||
            htmlColorMode === "light" ||
            htmlColorScheme === "light" ||
            bodyBsTheme === "light" ||
            (body && body.classList.contains("o_light_mode"))
        ) {
            return false;
        }

        // 2. Check explicit Dark Mode settings from Odoo Theme Switcher radio or classes
        if (
            htmlBsTheme === "dark" ||
            htmlColorMode === "dark" ||
            htmlColorScheme === "dark" ||
            bodyBsTheme === "dark" ||
            (body && body.classList.contains("o_dark_mode")) ||
            (body && body.classList.contains("o_web_client_dark")) ||
            (html && html.classList.contains("o_dark_mode"))
        ) {
            return true;
        }

        // 3. Fallback to OS system preference only if Odoo theme is not set
        return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    // Chart.js Rendering
    _initCharts() {
        this._destroyCharts();
        // eslint-disable-next-line no-undef
        if (typeof Chart === "undefined") return;

        const isDarkMode = this._isDarkMode();

        const textColor = isDarkMode ? "#94a3b8" : "#475569";
        const gridColor = isDarkMode ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.06)";
        const accentColor = isDarkMode ? "#00e5ff" : "#0284c7";

        // 1. Line Chart — Revenue Trend
        const canvasRevenue = document.getElementById("itMonthlyRevenueChart");
        if (canvasRevenue) {
            const ctx = canvasRevenue.getContext("2d");
            const data = this.state.chartsData.revenueTrend || [];

            const gradient = ctx.createLinearGradient(0, 0, 0, 250);
            if (isDarkMode) {
                gradient.addColorStop(0, "rgba(0, 229, 255, 0.35)");
                gradient.addColorStop(1, "rgba(0, 229, 255, 0.0)");
            } else {
                gradient.addColorStop(0, "rgba(2, 132, 199, 0.25)");
                gradient.addColorStop(1, "rgba(2, 132, 199, 0.0)");
            }

            // eslint-disable-next-line no-undef
            this.charts.revenueTrend = new Chart(canvasRevenue, {
                type: "line",
                data: {
                    labels: data.map(d => d.month || d.label),
                    datasets: [{
                        label: "Revenue ($)",
                        data: data.map(d => d.revenue),
                        borderColor: accentColor,
                        borderWidth: 3,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: accentColor,
                        pointRadius: 4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: () => this.onTileClick("sale.order", [], "Monthly Sales & Revenue"),
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor } }
                    }
                }
            });
        }

        // 3. Doughnut Chart — Technician Workload
        const canvasTech = document.getElementById("itTechnicianWorkloadChart");
        if (canvasTech) {
            const data = this.state.chartsData.technicianWorkload || [];
            // eslint-disable-next-line no-undef
            this.charts.technicianWorkload = new Chart(canvasTech, {
                type: "doughnut",
                data: {
                    labels: data.map(d => d.status),
                    datasets: [{
                        data: data.map(d => d.count),
                        backgroundColor: ["#7c4dff", "#00e5ff", "#ffab00"],
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: () => this.onTileClick("project.task", [], "Technician Workload Tasks"),
                    plugins: { legend: { position: "bottom", labels: { color: textColor } } }
                }
            });
        }

        // 4. Bar Chart — Service Type Volume
        const canvasServiceType = document.getElementById("itServiceTypeChart");
        if (canvasServiceType) {
            const data = this.state.chartsData.serviceTypeBreakdown || [];
            // eslint-disable-next-line no-undef
            this.charts.serviceType = new Chart(canvasServiceType, {
                type: "bar",
                data: {
                    labels: data.map(d => d.label),
                    datasets: [{
                        label: "Tickets",
                        data: data.map(d => d.count),
                        backgroundColor: ["#0284c7", "#7c4dff", "#ff4081", "#10b981", "#f59e0b"],
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: () => this.onTileClick("helpdesk.ticket", [], "Service Tickets"),
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor, precision: 0 } }
                    }
                }
            });
        }

        // 5. Polar Area Chart — Customer SLA Distribution
        const canvasSLA = document.getElementById("itCustomerServiceSLAChart");
        if (canvasSLA) {
            const data = this.state.chartsData.customerSLADistribution || [];
            // eslint-disable-next-line no-undef
            this.charts.customerSLA = new Chart(canvasSLA, {
                type: "polarArea",
                data: {
                    labels: data.map(d => d.tier),
                    datasets: [{
                        data: data.map(d => d.count),
                        backgroundColor: [
                            "rgba(0, 229, 255, 0.75)",
                            "rgba(124, 77, 255, 0.75)",
                            "rgba(255, 171, 0, 0.75)",
                            "rgba(255, 64, 129, 0.75)"
                        ],
                        borderWidth: 1,
                        borderColor: isDarkMode ? "#111827" : "#ffffff",
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: () => this.onTileClick("res.partner", [], "Customer SLA Distribution"),
                    plugins: { legend: { position: "bottom", labels: { color: textColor } } },
                    scales: {
                        r: { grid: { color: gridColor }, ticks: { display: false } }
                    }
                }
            });
        }

        // 6. Horizontal Grouped Bar Chart — Repair Cost Breakdown
        const canvasRepairCost = document.getElementById("itRepairCostChart");
        if (canvasRepairCost) {
            const data = this.state.chartsData.repairCostBreakdown || [];
            // eslint-disable-next-line no-undef
            this.charts.repairCost = new Chart(canvasRepairCost, {
                type: "bar",
                data: {
                    labels: data.map(d => d.job),
                    datasets: [
                        {
                            label: "Labour Cost ($)",
                            data: data.map(d => d.labour),
                            backgroundColor: "#8b5cf6",
                            borderRadius: 4,
                        },
                        {
                            label: "Spare Parts Cost ($)",
                            data: data.map(d => d.parts),
                            backgroundColor: "#00e5ff",
                            borderRadius: 4,
                        }
                    ]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: () => this.onTileClick("repair.order", [], "Repair Orders Cost Analysis"),
                    plugins: { legend: { position: "top", labels: { color: textColor } } },
                    scales: {
                        x: { grid: { color: gridColor }, ticks: { color: textColor } },
                        y: { grid: { color: gridColor }, ticks: { color: textColor } }
                    }
                }
            });
        }
    }

    onTileClick(model, domain, title) {
        const resolvedDomain = Array.isArray(domain) ? domain : JSON.parse(domain || "[]");
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            domain: resolvedDomain,
            target: "current",
        });
    }

    exportChartPNG(chartId, title) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        const link = document.createElement("a");
        link.download = `${title.replace(/\s+/g, "_")}.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    exportTableCSV(type) {
        let data = [];
        let headers = [];
        let filename = "";

        if (type === 'sales') {
            data = this.state.recentOrders;
            headers = ["Order Ref", "Customer", "Total Amount", "Status"];
            filename = "Recent_Sales_Orders.csv";
        } else if (type === 'schedule') {
            data = this.state.todaySchedule;
            headers = ["Time", "Customer", "Technician", "Service Type", "Status"];
            filename = "Today_Service_Schedule.csv";
        }

        if (data.length === 0) return;

        let csvContent = "data:text/csv;charset=utf-8," + headers.join(",") + "\n";
        data.forEach(item => {
            let row = [];
            if (type === 'sales') {
                row = [item.name, item.partner, item.amount, item.status];
            } else if (type === 'schedule') {
                row = [item.time, item.member, item.trainer, item.type, item.status];
            }
            csvContent += row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",") + "\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    _formatCurrency(val) {
        return `$${Number(val || 0).toLocaleString()}`;
    }
    _formatDate(dateStr) {
        if (!dateStr) return "—";
        return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    }
    _formatDateDisplay(d) {
        return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    }
    _formatTimeDisplay(d) {
        return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }
    _todayString() {
        const d = new Date();
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }
}

registry.category("actions").add("it_hardware_dashboard", ITHardwareDashboard);
