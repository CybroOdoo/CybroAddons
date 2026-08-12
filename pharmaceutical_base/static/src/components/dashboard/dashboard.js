/** @odoo-module **/

import {Component, onWillStart, useEffect, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {loadJS} from "@web/core/assets";
import {user} from "@web/core/user";

export class PharmaDashboard extends Component {
    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.chartRef = useRef("chartCanvas");
        this.statusChartRef = useRef("statusChartCanvas");

        // Bounds for the two date inputs in the header. Four digits max on the
        // year: without them the widget happily takes 5- and 6-digit years.
        this.dateMin = "1900-01-01";
        this.dateMax = "2999-12-31";

        const today = luxon.DateTime.local();
        const currentHour = today.hour;
        let greetingText = "Good morning";
        if (currentHour >= 12 && currentHour < 17) {
            greetingText = "Good afternoon";
        } else if (currentHour >= 17) {
            greetingText = "Good evening";
        }

        this.state = useState({
            userName: user.name || user.userName || "User",
            greeting: greetingText,

            // Rolling last-12-months window so the dashboard never goes blank
            // at a month boundary (data may predate the current month).
            startDate: today.minus({months: 11}).startOf("month").toFormat("yyyy-MM-dd"),
            endDate: today.endOf("month").toFormat("yyyy-MM-dd"),

            totalBatches: 0,
            openQcTests: 0,
            openDeviations: 0,
            openCapas: 0,
            openOos: 0,
            openQcSpecs: 0,

            // All-status counts (used by the "All Quality Activities" tiles).
            allQcTests: 0,
            allDeviations: 0,
            allCapas: 0,
            allOos: 0,
            totalQcSpecs: 0,

            // Whether the optional pharma_capa_deviation module is installed.
            // Deviation / CAPA tiles and activity boxes are hidden when false.
            capaAvailable: true,

            releasedBatches: 0,
            quarantineBatches: 0,
            rejectedBatches: 0,
            pendingReleaseBatches: 0,
            statusPercent: 0,

            expiringToday: 0,
            expiring30: 0,
            expiring60: 0,
            expiring90: 0,

            incomingQcPending: 0,
            ipqcQcTotal: 0,
            finishedQcReleased: 0,

            recentBatches: [],

            chartLabels: ["Dec", "Jan", "Feb", "Mar", "Apr", "May"],
            chartData: [82, 96, 108, 95, 125, 148],   // Released (done) per bucket
            chartWip: [0, 0, 0, 0, 0, 0],              // In-process per bucket

            trendBatches: {value: 0, up: true},
            trendQc: {value: 0, up: true},
            trendDev: {value: 0, up: true},
            trendCapa: {value: 0, up: true},
            trendOos: {value: 0, up: true},

            chartFilter: "daily",

            // Dynamic Calendar state
            calBaseDate: today.startOf("week"),
            calDays: [],
            selectedCalDate: null,
        });

        this.updateCalDays();

        onWillStart(async () => {
            if (user.name) {
                this.state.userName = user.name;
            } else {
                try {
                    const userData = await this.orm.read("res.users", [user.userId], ["name"]);
                    if (userData && userData.length > 0) {
                        this.state.userName = userData[0].name;
                    }
                } catch (e) {
                    // Fallback
                }
            }
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.fetchData();
        });

        useEffect(() => {
            this.renderChart();
        }, () => [this.state.chartData, this.state.chartWip]);

        useEffect(() => {
            this.renderStatusChart();
        }, () => [
            this.state.releasedBatches, this.state.quarantineBatches,
            this.state.rejectedBatches, this.state.pendingReleaseBatches,
        ]);
    }

    async fetchData() {
        const startStr = this.state.startDate + " 00:00:00";
        const endStr = this.state.endDate + " 23:59:59";

        // Sync calendar row selection state with current date range
        if (this.state.startDate !== this.state.endDate) {
            this.state.selectedCalDate = null;
        }
        this.updateCalDays();

        // Trend chart buckets both series (Released / In-process) on the SAME
        // field so their categories line up exactly.
        const chartField = "create_date";
        let interval = "month";
        if (this.state.chartFilter === "yearly") interval = "year";
        else if (this.state.chartFilter === "weekly") interval = "week";
        else if (this.state.chartFilter === "daily") interval = "day";
        const groupBy = `${chartField}:${interval}`;
        const countKey = `${chartField}_count`;

        const startDT = luxon.DateTime.fromISO(this.state.startDate);
        const endDT = luxon.DateTime.fromISO(this.state.endDate);
        const diffDays = endDT.diff(startDT, 'days').days;

        const prevStartStr = startDT.minus({days: diffDays + 1}).toFormat("yyyy-MM-dd") + " 00:00:00";
        const prevEndStr = startDT.minus({days: 1}).toFormat("yyyy-MM-dd") + " 23:59:59";

        const today = luxon.DateTime.local();
        const todayEndStr = today.endOf("day").toFormat("yyyy-MM-dd HH:mm:ss");
        const todayStartStr = today.startOf("day").toFormat("yyyy-MM-dd HH:mm:ss");
        const in30 = today.plus({days: 30}).toFormat("yyyy-MM-dd HH:mm:ss");
        const in60 = today.plus({days: 60}).toFormat("yyyy-MM-dd HH:mm:ss");
        const in90 = today.plus({days: 90}).toFormat("yyyy-MM-dd HH:mm:ss");

        const dateDomain = [["create_date", ">=", startStr], ["create_date", "<=", endStr]];
        const prevDateDomain = [["create_date", ">=", prevStartStr], ["create_date", "<=", prevEndStr]];

        const [
            totalBatches, openQcTests, openDeviations, openCapas, openOos, openQcSpecs,
            releasedBatches, quarantineBatches, rejectedBatches, pendingReleaseBatches,
            expiringToday, expiring30, expiring60, expiring90,
            productionDone, productionWip, recentBatches,

            tmBatches, tmQc, tmDev, tmCapa, tmOos,
            lmBatches, lmQc, lmDev, lmCapa, lmOos,
            totalQcSpecs,
            incomingQcPending, ipqcQcTotal, ipqcResultTotal, finishedQcReleased
        ] = await Promise.all([
            // Current Period
            this.orm.searchCount("stock.lot", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.qc.test.order", [["status", "in", ["draft", "in_progress", "under_investigation"]], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("pharma.deviation", [["status", "in", ["open", "under_investigation"]], ...dateDomain]).catch(() => {
                this.state.capaAvailable = false;
                return 0;
            }),
            this.orm.searchCount("pharma.capa", [["status", "in", ["open", "under_investigation"]], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("pharma.oos.investigation", [["closed_on", "=", false], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("pharma.qc.spec", [["state", "in", ["draft", "review"]], ...dateDomain]).catch(() => 0),

            // Statuses
            this.orm.searchCount("stock.lot", [["lot_status", "=", "released"], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["lot_status", "=", "quarantine"], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["lot_status", "=", "rejected"], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["lot_status", "=", "approved"], ...dateDomain]).catch(() => 0),

            // Expiring — buckets are cumulative and all start at the beginning of
            // today, so a lot expiring today is also counted in the 30/60/90 windows.
            this.orm.searchCount("stock.lot", [["expiration_date", "<=", todayEndStr], ["expiration_date", ">=", todayStartStr]]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["expiration_date", "<=", in30], ["expiration_date", ">=", todayStartStr]]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["expiration_date", "<=", in60], ["expiration_date", ">=", todayStartStr]]).catch(() => 0),
            this.orm.searchCount("stock.lot", [["expiration_date", "<=", in90], ["expiration_date", ">=", todayStartStr]]).catch(() => 0),

            // Chart — Released (done) per bucket
            this.orm.call("mrp.production", "read_group", [[["state", "=", "done"],
                [chartField, ">=", startStr], [chartField, "<=", endStr]], ["id"], [groupBy]]).catch(() => []),
            // Chart — In-process (not done / not cancelled) per bucket
            this.orm.call("mrp.production", "read_group", [[["state", "in", ["confirmed", "progress", "to_close"]],
                [chartField, ">=", startStr], [chartField, "<=", endStr]], ["id"], [groupBy]]).catch(() => []),

            // Recent batches: the most recently created lots, any status.
            this.orm.searchRead("stock.lot",
                [],
                ["id", "name", "lot_status", "product_id", "create_date", "manufacture_date"],
                {limit: 6, order: "create_date desc"}).catch(() => []),

            // This period creations for trend
            this.orm.searchCount("stock.lot", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.qc.test.order", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.deviation", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.capa", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.oos.investigation", dateDomain).catch(() => 0),

            // Previous period creations for trend
            this.orm.searchCount("stock.lot", prevDateDomain).catch(() => 0),
            this.orm.searchCount("pharma.qc.test.order", prevDateDomain).catch(() => 0),
            this.orm.searchCount("pharma.deviation", prevDateDomain).catch(() => 0),
            this.orm.searchCount("pharma.capa", prevDateDomain).catch(() => 0),
            this.orm.searchCount("pharma.oos.investigation", prevDateDomain).catch(() => 0),
            this.orm.searchCount("pharma.qc.spec", [["state", "=", "approved"], ...dateDomain]).catch(() => 0),

            // Stage-specific QC Test Order & IPQC Result counts within selected date filter
            this.orm.searchCount("pharma.qc.test.order", [["stage", "=", "incoming"], ["status", "in", ["draft", "in_progress", "under_investigation"]], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("pharma.qc.test.order", [["stage", "=", "inprocess"], ...dateDomain]).catch(() => 0),
            this.orm.searchCount("pharma.ipqc.result", dateDomain).catch(() => 0),
            this.orm.searchCount("pharma.qc.test.order", [["stage", "=", "finished"], ["status", "=", "passed"], ...dateDomain]).catch(() => 0)
        ]);

        const calcTrend = (tm, lm) => {
            if (lm === 0) return tm > 0 ? {value: 100, up: true} : {value: 0, up: true};
            const diff = ((tm - lm) / lm) * 100;
            return {value: Math.abs(Math.round(diff)), up: diff >= 0};
        };

        this.state.trendBatches = calcTrend(tmBatches, lmBatches);
        this.state.trendQc = calcTrend(tmQc, lmQc);
        this.state.trendDev = calcTrend(tmDev, lmDev);
        this.state.trendCapa = calcTrend(tmCapa, lmCapa);
        this.state.trendOos = calcTrend(tmOos, lmOos);

        this.state.totalBatches = totalBatches;
        this.state.openQcTests = openQcTests;
        this.state.openDeviations = openDeviations;
        this.state.openCapas = openCapas;
        this.state.openOos = openOos;
        this.state.openQcSpecs = openQcSpecs;

        this.state.incomingQcPending = incomingQcPending;
        this.state.ipqcQcTotal = (ipqcQcTotal || 0) + (ipqcResultTotal || 0);
        this.state.finishedQcReleased = finishedQcReleased;

        // All-status counts within the selected period (reuse the trend counts).
        this.state.allQcTests = tmQc;
        this.state.allDeviations = tmDev;
        this.state.allCapas = tmCapa;
        this.state.allOos = tmOos;
        this.state.totalQcSpecs = totalQcSpecs;

        this.state.releasedBatches = releasedBatches;
        this.state.quarantineBatches = quarantineBatches;
        this.state.rejectedBatches = rejectedBatches;
        this.state.pendingReleaseBatches = pendingReleaseBatches;

        const statusTotal = releasedBatches + quarantineBatches + rejectedBatches + pendingReleaseBatches;
        this.state.statusPercent = statusTotal ? Math.round((releasedBatches / statusTotal) * 100) : 0;

        this.state.expiringToday = expiringToday;
        this.state.expiring30 = expiring30;
        this.state.expiring60 = expiring60;
        this.state.expiring90 = expiring90;

        const statusLabels = {
            quarantine: "Quarantine", approved: "Approved", released: "Released",
            rejected: "Rejected", on_hold: "On Hold", recalled: "Recalled",
        };
        const fmtMfg = (val) => {
            if (!val) return "—";
            const dt = luxon.DateTime.fromISO(String(val).replace(" ", "T"));
            return dt.isValid ? dt.toFormat("MMM dd") : "—";
        };
        this.state.recentBatches = (recentBatches || []).map((lot) => ({
            id: lot.id,
            name: lot.name || `#${lot.id}`,
            product: lot.product_id ? lot.product_id[1] : "",
            mfgDate: fmtMfg(lot.manufacture_date || lot.create_date),
            statusLabel: statusLabels[lot.lot_status] || lot.lot_status,
            status: lot.lot_status,
        }));

        // Merge the two series (Released / In-process) on a shared, ordered set
        // of bucket keys so bars align. read_group returns groups in ascending
        // chronological order.
        const order = [];
        const relMap = {};
        const wipMap = {};
        const collect = (rows, map) => {
            for (const item of rows || []) {
                const key = item[groupBy];
                if (!key) continue;
                const k = String(key);
                map[k] = (map[k] || 0) + (item[countKey] || 0);
                if (!order.includes(k)) order.push(k);
            }
        };
        collect(productionDone, relMap);
        collect(productionWip, wipMap);

        if (order.length > 0) {
            const keys = order.slice(-30);
            this.state.chartLabels = keys.map((k) => k.split(" ")[0]);
            this.state.chartData = keys.map((k) => relMap[k] || 0);
            this.state.chartWip = keys.map((k) => wipMap[k] || 0);
        } else {
            this.state.chartLabels = ["No Data"];
            this.state.chartData = [0];
            this.state.chartWip = [0];
        }
    }

    renderChart() {
        if (!this.chartRef.el) return;
        const ctx = this.chartRef.el.getContext("2d");

        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        this.chartInstance = new Chart(ctx, {
            type: "bar",
            data: {
                labels: this.state.chartLabels,
                datasets: [
                    {
                        label: "Released",
                        data: this.state.chartData,
                        backgroundColor: "#5295f8",   // Primary #5295f8
                        borderRadius: 4,
                        borderSkipped: false,
                        maxBarThickness: 26,
                    },
                    {
                        label: "In process",
                        data: this.state.chartWip,
                        backgroundColor: "#93c5fd",   // Light Soft Blue
                        borderRadius: 4,
                        borderSkipped: false,
                        maxBarThickness: 26,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: "bottom",
                        align: "start",
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            usePointStyle: true,
                            pointStyle: "rectRounded",
                            color: "#1f2937",
                            font: {size: 11, weight: "bold"},
                        },
                    },
                    tooltip: {
                        backgroundColor: "#5295f8",
                        titleColor: "#ffffff",
                        bodyColor: "#ffffff",
                        padding: 10,
                        cornerRadius: 8,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 10,
                        grid: {color: "rgba(82, 149, 248, 0.12)"},
                        ticks: {color: "#6b7280", precision: 0},
                    },
                    x: {
                        grid: {display: false},
                        ticks: {color: "#6b7280", maxRotation: 0, autoSkip: true, maxTicksLimit: 12},
                    }
                }
            }
        });
    }

    renderStatusChart() {
        if (!this.statusChartRef.el) return;
        const ctx = this.statusChartRef.el.getContext("2d");

        if (this.statusChartInstance) {
            this.statusChartInstance.destroy();
        }

        // Anchor the tooltip just OUTSIDE the hovered arc so it never covers the
        // centre "% Released" label sitting in the doughnut hole. Registered
        // once on the shared tooltip plugin (idempotent across re-renders).
        const tooltipPlugin = Chart.registry.getPlugin("tooltip");
        if (tooltipPlugin && !tooltipPlugin.positioners.pharmaOutside) {
            tooltipPlugin.positioners.pharmaOutside = function (elements) {
                if (!elements.length) return false;
                const arc = elements[0].element;
                const angle = (arc.startAngle + arc.endAngle) / 2;
                const r = arc.outerRadius + 6;
                return {
                    x: arc.x + Math.cos(angle) * r,
                    y: arc.y + Math.sin(angle) * r,
                };
            };
        }

        const values = [
            this.state.releasedBatches,
            this.state.pendingReleaseBatches,
            this.state.quarantineBatches,
            this.state.rejectedBatches,
        ];
        const empty = values.every((v) => !v);

        this.statusChartInstance = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: ["Released", "Pending Release", "Quarantine", "Rejected"],
                datasets: [{
                    data: empty ? [1] : values,
                    backgroundColor: empty
                        ? ["#e5e7eb"]
                        : ["#5295f8", "#93c5fd", "#60a5fa", "#cbd5e1"],
                    borderWidth: 0,
                    hoverOffset: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                // Small inset so an outside-anchored tooltip stays on-canvas.
                layout: {padding: 8},
                plugins: {
                    legend: {display: false},
                    tooltip: {
                        enabled: !empty,
                        position: "pharmaOutside",
                        caretPadding: 6,
                        backgroundColor: "#16283F",
                        bodyColor: "#ffffff",
                        padding: 10,
                        cornerRadius: 8,
                    },
                },
            }
        });
    }

    // --- Action Handlers for Clicks ---

    getDateDomain() {
        const startStr = this.state.startDate + " 00:00:00";
        const endStr = this.state.endDate + " 23:59:59";
        return [["create_date", ">=", startStr], ["create_date", "<=", endStr]];
    }

    openLots() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Batches",
            res_model: "stock.lot",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openQcTests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open QC Tests",
            res_model: "pharma.qc.test.order",
            domain: [["status", "in", ["draft", "in_progress", "under_investigation"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openDeviations() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open Deviations",
            res_model: "pharma.deviation",
            domain: [["status", "in", ["open", "under_investigation"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openCapas() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open CAPAs",
            res_model: "pharma.capa",
            domain: [["status", "in", ["open", "under_investigation"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openOos() {
        this.openAllOos();
    }

    openAllOos() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open OOS Investigations",
            res_model: "pharma.oos.investigation",
            domain: [["closed_on", "=", false], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openAllCapas() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open CAPAs",
            res_model: "pharma.capa",
            domain: [["status", "not in", ["closed", "done", "cancelled"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openAllDeviations() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open Deviations",
            res_model: "pharma.deviation",
            domain: [["status", "not in", ["closed", "done", "cancelled"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openAllQcTests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open QC Tests",
            res_model: "pharma.qc.test.order",
            domain: [["status", "in", ["draft", "in_progress", "under_investigation"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openIncomingQcTests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Incoming QC Tests",
            res_model: "pharma.qc.test.order",
            domain: [["stage", "=", "incoming"], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    async openIpqcTests() {
        const dateDomain = this.getDateDomain();
        const ipqcResultCount = await this.orm.searchCount("pharma.ipqc.result", dateDomain).catch(() => 0);
        if (ipqcResultCount > 0) {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "IPQC In-Process Controls",
                res_model: "pharma.ipqc.result",
                domain: dateDomain,
                views: [[false, "list"], [false, "form"]],
            });
        } else {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: "IPQC Products QC",
                res_model: "pharma.qc.test.order",
                domain: [["stage", "=", "inprocess"], ...dateDomain],
                views: [[false, "list"], [false, "form"]],
            });
        }
    }

    openFinishedQcTests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Finished Products QC",
            res_model: "pharma.qc.test.order",
            domain: [["stage", "=", "finished"], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openQcSpecs() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Open QC Specifications",
            res_model: "pharma.qc.spec",
            domain: [["state", "not in", ["approved","rejected"]], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    totalQcSpecs() {
        this.openTotalQcSpecs();
    }

    openTotalOos() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All OOS Investigations",
            res_model: "pharma.oos.investigation",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openTotalCapas() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All CAPAs",
            res_model: "pharma.capa",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openTotalDeviations() {
        if (!this.state.capaAvailable) return;
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All Deviations",
            res_model: "pharma.deviation",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openTotalQcTests() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All QC Tests",
            res_model: "pharma.qc.test.order",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openTotalQcSpecs() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "All QC Specifications",
            res_model: "pharma.qc.spec",
            domain: [...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openLotsByStatus(status) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: `Batches - ${status}`,
            res_model: "stock.lot",
            domain: [["lot_status", "=", status], ...this.getDateDomain()],
            views: [[false, "list"], [false, "form"]],
        });
    }

    openLot(lotId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Batch",
            res_model: "stock.lot",
            res_id: lotId,
            views: [[false, "form"]],
        });
    }

    openExpiringLots(days) {
        const today = luxon.DateTime.local();
        // All windows start at the beginning of today (matches the tile counts),
        // so lots expiring today are included in the 30/60/90 lists too.
        const start = today.startOf("day").toFormat("yyyy-MM-dd HH:mm:ss");
        let end;
        if (days === 0) {
            end = today.endOf("day").toFormat("yyyy-MM-dd HH:mm:ss");
        } else {
            end = today.plus({days}).toFormat("yyyy-MM-dd HH:mm:ss");
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: `Expiring within ${days} days`,
            res_model: "stock.lot",
            domain: [["expiration_date", "<=", end], ["expiration_date", ">=", start]],
            views: [[false, "list"], [false, "form"]],
        });
    }

    updateCalDays() {
        const today = luxon.DateTime.local();
        const selectedStr = this.state.selectedCalDate ||
            (this.state.startDate === this.state.endDate ? this.state.startDate : null);
        const days = [];
        let cur = this.state.calBaseDate;
        for (let i = 0; i < 7; i++) {
            const dateStr = cur.toFormat("yyyy-MM-dd");
            const isToday = cur.hasSame(today, "day");
            const isSelected = selectedStr ? (dateStr === selectedStr) : isToday;
            days.push({
                dow: cur.toFormat("ccc").slice(0, 2),
                num: cur.toFormat("dd"),
                date: dateStr,
                isToday: isToday,
                isSelected: isSelected,
            });
            cur = cur.plus({days: 1});
        }
        this.state.calDays = days;
    }

    prevCalWeek() {
        this.state.calBaseDate = this.state.calBaseDate.minus({weeks: 1});
        this.updateCalDays();
    }

    nextCalWeek() {
        this.state.calBaseDate = this.state.calBaseDate.plus({weeks: 1});
        this.updateCalDays();
    }

    selectCalDay(day) {
        this.state.selectedCalDate = day.date;
        this.state.startDate = day.date;
        this.state.endDate = day.date;
        this.updateCalDays();
        this.fetchData();
    }

    setChartFilter(filter) {
        this.state.chartFilter = filter;
        this.fetchData();
    }

    /**
     * Date range change coming from either of the two native date inputs.
     *
     * The inputs are bound with min/max, but a browser will still hand over an
     * out-of-range value when the year is typed instead of stepped — Chrome's
     * year field accepts up to six digits — so the range is clamped here too
     * before it reaches any read_group domain.
     */
    onDateChange() {
        this.state.startDate = this.clampDate(this.state.startDate, this.dateMin);
        this.state.endDate = this.clampDate(this.state.endDate, this.dateMax);
        // A backwards range silently matches nothing; keep it ordered.
        if (this.state.endDate < this.state.startDate) {
            this.state.endDate = this.state.startDate;
        }
        this.fetchData();
    }

    /**
     * Keep a yyyy-MM-dd string within [dateMin, dateMax]. Values luxon cannot
     * parse — an empty input, or a 5+ digit year, which ISO 8601 only allows
     * with an explicit sign — fall back to `fallback`.
     */
    clampDate(value, fallback) {
        const dt = luxon.DateTime.fromISO(value || "");
        if (!dt.isValid) {
            return fallback;
        }
        if (dt < luxon.DateTime.fromISO(this.dateMin)) {
            return this.dateMin;
        }
        if (dt > luxon.DateTime.fromISO(this.dateMax)) {
            return this.dateMax;
        }
        return dt.toFormat("yyyy-MM-dd");
    }
}

PharmaDashboard.template = "pharmaceutical_base.PharmaDashboard";

registry.category("actions").add("pharma_dashboard_action", PharmaDashboard);
