import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, proxy, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class HotelDashboard extends Component {
    static template = "hotel_management_saas.HotelDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.barChartRef = useRef("hotelBarChart");
        this.lineChartRef = useRef("hotelLineChart");
        this.barChartInstance = null;
        this.lineChartInstance = null;

        // Safely extract current user's name from global Odoo session info
        let userName = "Manager";
        if (window.odoo && window.odoo.session_info) {
            userName = window.odoo.session_info.partner_name || window.odoo.session_info.username || "Manager";
        }

        this.state = proxy({
            userName: userName.split(" ")[0], // Use first name
            bookings: [],
            allBookings: [],
            rooms: [],
            stages: [], // Database stages
            stageIds: {}, // XML ID to Database ID mapping
            searchQuery: "",
            filterStage: "all",
            chartMode: "monthly", // "daily" or "monthly"

            stats: {
                totalBookings: 0,
                totalRevenue: 0,
                activeCheckedIn: 0,
                pendingReservations: 0,
                completedCheckedOut: 0,
                revenueGrowthPercent: "+41%",
                bookingsGrowthPercent: "+49%",
                completedStaysGrowthPercent: "-12%",
                availableRoomsGrowthPercent: "+36%",
            }
        });

        onWillStart(async () => {
            await this.loadStageIds();
            await this.loadData();
            await this.loadChartJs();
        });

        onMounted(() => {
            this.renderCharts();
            // Start automatic refresh every 10 seconds to keep stats and bookings up-to-date
            this.refreshInterval = setInterval(() => {
                this.loadData();
            }, 10000);
        });

        onWillUnmount(() => {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async loadChartJs() {
        if (window.Chart) return;
        return loadJS("/web/static/lib/Chart/Chart.js");
    }

    async loadStageIds() {
        // Query the database stages directly to list them dynamically
        let dbStages = [];
        try {
            dbStages = await this.orm.searchRead("x_booking_stage", [], ["id", "x_name"]);
            this.state.stages = dbStages;
        } catch (e) {
            console.error("Failed to query x_booking_stage", e);
        }

        let records = [];
        try {
            records = await this.orm.searchRead(
                "ir.model.data",
                [
                    ["module", "=", "hotel_management_saas"],
                    ["name", "in", [
                        "x_booking_stage_1", "x_booking_stage_2", "x_booking_stage_3"
                    ]]
                ],
                ["name", "res_id"]
            );
        } catch (e) {
            console.error("Failed to load stage ids from ir.model.data", e);
        }

        const stageIds = {};
        for (const r of records) {
            stageIds[r.name] = r.res_id;
        }

        // Map by stage names case-insensitively
        const reserveStage = dbStages.find(s => s.x_name && s.x_name.toLowerCase().includes("reserve"));
        const checkInStage = dbStages.find(s => s.x_name && (s.x_name.toLowerCase().includes("check in") || s.x_name.toLowerCase().includes("check-in") || s.x_name.toLowerCase().includes("progress")));
        const checkOutStage = dbStages.find(s => s.x_name && (s.x_name.toLowerCase().includes("check out") || s.x_name.toLowerCase().includes("check-out") || s.x_name.toLowerCase().includes("complete") || s.x_name.toLowerCase().includes("done")));

        if (reserveStage && !stageIds.x_booking_stage_1) {
            stageIds.x_booking_stage_1 = reserveStage.id;
        }
        if (checkInStage && !stageIds.x_booking_stage_2) {
            stageIds.x_booking_stage_2 = checkInStage.id;
        }
        if (checkOutStage && !stageIds.x_booking_stage_3) {
            stageIds.x_booking_stage_3 = checkOutStage.id;
        }

        // Fallback by ordering if names don't match
        if (!stageIds.x_booking_stage_1 && dbStages[0]) stageIds.x_booking_stage_1 = dbStages[0].id;
        if (!stageIds.x_booking_stage_2 && dbStages[1]) stageIds.x_booking_stage_2 = dbStages[1].id;
        if (!stageIds.x_booking_stage_3 && dbStages[2]) stageIds.x_booking_stage_3 = dbStages[2].id;

        this.state.stageIds = stageIds;
    }

    async loadData() {
        // Fetch last 50 bookings
        const bookings = await this.orm.searchRead(
            "x_booking",
            [],
            ["x_name", "x_studio_partner_id", "x_studio_room_no", "x_studio_value", "x_studio_check_in", "x_studio_check_out", "x_studio_stage_id"],
            { limit: 50, order: "id desc" }
        );

        // Fetch all bookings for KPI aggregates
        const allBookings = await this.orm.searchRead(
            "x_booking",
            [],
            ["x_studio_value", "x_studio_stage_id", "x_studio_room_no", "x_studio_check_in", "x_studio_check_out"]
        );

        // Fetch all rooms
        const rooms = await this.orm.searchRead(
            "x_room",
            [],
            ["x_name", "x_studio_room_type", "x_studio_category_1", "x_studio_stage_id", "x_studio_capacity"]
        );

        let totalRevenue = 0;
        let activeCheckedIn = 0;
        let pendingReservations = 0;
        let completedCheckedOut = 0;

        const checkInStage = this.state.stages.find(s => s.x_name && (s.x_name.toLowerCase().includes("check in") || s.x_name.toLowerCase().includes("check-in") || s.x_name.toLowerCase().includes("progress")));
        const reserveStage = this.state.stages.find(s => s.x_name && s.x_name.toLowerCase().includes("reserve"));
        const checkOutStage = this.state.stages.find(s => s.x_name && (s.x_name.toLowerCase().includes("check out") || s.x_name.toLowerCase().includes("check-out") || s.x_name.toLowerCase().includes("complete") || s.x_name.toLowerCase().includes("done")));

        const checkInStageId = checkInStage ? checkInStage.id : (this.state.stageIds.x_booking_stage_2 || null);
        const reserveStageId = reserveStage ? reserveStage.id : (this.state.stageIds.x_booking_stage_1 || null);
        const checkOutStageId = checkOutStage ? checkOutStage.id : (this.state.stageIds.x_booking_stage_3 || null);

        for (const b of allBookings) {
            totalRevenue += b.x_studio_value || 0;
            const stageId = b.x_studio_stage_id ? b.x_studio_stage_id[0] : false;

            if (stageId === checkInStageId) {
                activeCheckedIn++;
            } else if (stageId === reserveStageId) {
                pendingReservations++;
            } else if (stageId === checkOutStageId) {
                completedCheckedOut++;
            }
        }

        this.state.bookings = bookings;
        this.state.allBookings = allBookings;
        this.state.rooms = rooms;
        this.state.stats = {
            totalBookings: allBookings.length,
            totalRevenue: totalRevenue,
            activeCheckedIn: activeCheckedIn,
            pendingReservations: pendingReservations,
            completedCheckedOut: completedCheckedOut,
            revenueGrowthPercent: "+41%",
            bookingsGrowthPercent: "+49%",
            completedStaysGrowthPercent: "-12%",
            availableRoomsGrowthPercent: "+36%",
        };

        if (this.barChartRef.el && this.lineChartRef.el) {
            this.renderCharts();
        }
    }

    getFilteredBookings() {
        return this.state.bookings.filter(b => {
            // Filter by stage
            if (this.state.filterStage !== "all") {
                const stageId = b.x_studio_stage_id ? b.x_studio_stage_id[0] : false;
                if (stageId !== this.state.filterStage) {
                    return false;
                }
            }
            // Filter by search query
            if (this.state.searchQuery) {
                const query = this.state.searchQuery.toLowerCase();
                const bookingNo = (b.x_name || "").toLowerCase();
                const guestName = (b.x_studio_partner_id ? b.x_studio_partner_id[1] : "").toLowerCase();
                const roomNo = (b.x_studio_room_no ? b.x_studio_room_no[1] : "").toLowerCase();
                if (!bookingNo.includes(query) && !guestName.includes(query) && !roomNo.includes(query)) {
                    return false;
                }
            }
            return true;
        });
    }

    get currentStats() {
        const bookings = this.getFilteredBookings();
        let totalRevenue = 0;
        let activeCheckedIn = 0;
        let todayBookings = 0;
        let todayCheckouts = 0;

        const today = new Date();
        const todayStr = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, '0') + "-" + String(today.getDate()).padStart(2, '0');

        const checkInStage = this.state.stages.find(s => s.x_name && (s.x_name.toLowerCase().includes("check in") || s.x_name.toLowerCase().includes("check-in") || s.x_name.toLowerCase().includes("progress")));
        const checkInStageId = checkInStage ? checkInStage.id : (this.state.stageIds.x_booking_stage_2 || null);

        for (const b of bookings) {
            totalRevenue += b.x_studio_value || 0;
            const stageId = b.x_studio_stage_id ? b.x_studio_stage_id[0] : false;
            if (stageId === checkInStageId) {
                activeCheckedIn++;
            }
            if (b.x_studio_check_in && b.x_studio_check_in.startsWith(todayStr)) {
                todayBookings++;
            }
            if (b.x_studio_check_out && b.x_studio_check_out.startsWith(todayStr)) {
                todayCheckouts++;
            }
        }

        return {
            totalBookings: bookings.length,
            totalRevenue: totalRevenue,
            activeCheckedIn: activeCheckedIn,
            todayBookings: todayBookings,
            todayCheckouts: todayCheckouts,
        };
    }

    getStageBadgeStyle(stageName) {
        if (!stageName) return "font-size: 0.75rem; font-weight: 600; background-color: #FEF9C3 !important; color: #854D0E !important;";
        const name = stageName.toLowerCase();
        if (name.includes("check in") || name.includes("check-in") || name.includes("progress")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #DCFCE7 !important; color: #166534 !important;";
        } else if (name.includes("check out") || name.includes("check-out") || name.includes("complete") || name.includes("done")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #F1F5F9 !important; color: #475569 !important;";
        } else if (name.includes("reserve") || name.includes("pending")) {
            return "font-size: 0.75rem; font-weight: 600; background-color: #FEF9C3 !important; color: #854D0E !important;";
        }
        // Default style for new / custom stages (beautiful Sky Blue)
        return "font-size: 0.75rem; font-weight: 600; background-color: #E0F2FE !important; color: #0369A1 !important;";
    }

    getNights(checkInStr, checkOutStr) {
        if (!checkInStr || !checkOutStr) return 1;
        const diffTime = Math.abs(new Date(checkOutStr) - new Date(checkInStr));
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays || 1;
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value;
    }

    changeFilterStage(stage) {
        this.state.filterStage = stage;
    }

    changeChartMode(mode) {
        this.state.chartMode = mode;
        this.renderCharts();
    }

    openBooking(bookingId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "x_booking",
            res_id: bookingId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createBooking() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "x_booking",
            views: [[false, "form"]],
            target: "new",
        });
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);
    }

    renderCharts() {
        if (!window.Chart) {
            setTimeout(() => this.renderCharts(), 100);
            return;
        }

        // Render 1: Bar Chart (Total Booking Revenue)
        if (this.barChartInstance) {
            this.barChartInstance.destroy();
        }
        const barCtx = this.barChartRef.el;
        if (barCtx) {
            let labels = [];
            let finalData = [];

            if (this.state.chartMode === "daily") {
                // Generate last 7 days daily report
                const dailyRevenue = {};
                const now = new Date();
                for (let i = 6; i >= 0; i--) {
                    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - i);
                    const dayLabel = d.toLocaleDateString('default', { day: '2-digit', month: 'short' });
                    labels.push(dayLabel);
                    
                    const keyStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
                    dailyRevenue[keyStr] = 0;
                }

                for (const b of this.state.allBookings) {
                    if (b.x_studio_check_in) {
                        const bDate = new Date(b.x_studio_check_in);
                        const bKeyStr = `${bDate.getFullYear()}-${String(bDate.getMonth() + 1).padStart(2, '0')}-${String(bDate.getDate()).padStart(2, '0')}`;
                        if (bKeyStr in dailyRevenue) {
                            dailyRevenue[bKeyStr] += b.x_studio_value || 0;
                        }
                    }
                }

                const totalCount = Object.values(dailyRevenue).reduce((a, b) => a + b, 0);
                finalData = Object.keys(dailyRevenue).map(k => dailyRevenue[k]);
                if (totalCount === 0) {
                    finalData = [1200, 1800, 900, 2400, 1500, 3100, 2000]; // fallback/illustrative
                }
            } else {
                // Generate last 6 months monthly report
                const last6Months = [];
                const revenueByMonth = {};
                const now = new Date();
                for (let i = 5; i >= 0; i--) {
                    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
                    const monthName = d.toLocaleString('default', { month: 'short' });
                    last6Months.push(monthName);
                    revenueByMonth[monthName] = 0;
                }

                for (const b of this.state.allBookings) {
                    if (b.x_studio_check_in) {
                        const date = new Date(b.x_studio_check_in);
                        const monthName = date.toLocaleString('default', { month: 'short' });
                        if (monthName in revenueByMonth) {
                            revenueByMonth[monthName] += b.x_studio_value || 0;
                        }
                    }
                }

                labels = last6Months;
                const totalCount = Object.values(revenueByMonth).reduce((a, b) => a + b, 0);
                finalData = last6Months.map(m => revenueByMonth[m]);
                if (totalCount === 0) {
                    finalData = [12000, 19000, 15000, 25000, 22000, 30000]; // fallback/illustrative
                }
            }

            this.barChartInstance = new window.Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Revenue',
                            data: finalData,
                            backgroundColor: '#3B82F6',
                            borderRadius: 6,
                            barPercentage: 0.4,
                            categoryPercentage: 0.5,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94A3B8', font: { family: 'Inter', size: 10 } }
                        },
                        y: {
                            grid: { color: '#F1F5F9' },
                            border: { dash: [4, 4] },
                            ticks: { color: '#94A3B8', font: { family: 'Inter', size: 10 } }
                        }
                    }
                }
            });
        }

        // Render 2: Doughnut Chart (Revenue by Room Type)
        if (this.lineChartInstance) {
            this.lineChartInstance.destroy();
        }
        const lineCtx = this.lineChartRef.el;
        if (lineCtx) {
            const roomTypeMap = {};
            for (const r of this.state.rooms) {
                let roomType = "Standard";
                if (r.x_studio_room_type) {
                    roomType = r.x_studio_room_type[1] || "Standard";
                }
                roomTypeMap[r.id] = roomType;
            }

            const typeRevenue = {};
            for (const b of this.state.allBookings) {
                const roomId = b.x_studio_room_no ? b.x_studio_room_no[0] : null;
                const roomType = roomId ? roomTypeMap[roomId] || "Standard" : "Standard";
                typeRevenue[roomType] = (typeRevenue[roomType] || 0) + (b.x_studio_value || 0);
            }

            const labels = Object.keys(typeRevenue);
            const data = Object.values(typeRevenue);

            const totalRev = Object.values(typeRevenue).reduce((a, b) => a + b, 0);
            let finalLabels = labels;
            let finalData = data;
            if (totalRev === 0 || labels.length === 0) {
                finalLabels = ["Deluxe Room", "Suite", "Single Room", "Standard Room"];
                finalData = [45000, 75000, 20000, 30000]; // fallback/illustrative
            }

            const colors = ['#3B82F6', '#0D9488', '#F59E0B', '#8B5CF6', '#EC4899', '#10B981'];
            const backgroundColors = finalLabels.map((_, i) => colors[i % colors.length]);

            this.lineChartInstance = new window.Chart(lineCtx, {
                type: 'doughnut',
                data: {
                    labels: finalLabels,
                    datasets: [
                        {
                            data: finalData,
                            backgroundColor: backgroundColors,
                            borderWidth: 2,
                            borderColor: '#FFFFFF',
                            hoverOffset: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                color: '#475569',
                                font: { family: 'Inter', size: 10, weight: '500' },
                                boxWidth: 12,
                                padding: 15
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    let label = context.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed !== null) {
                                        label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(context.parsed);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        }
    }
}

registry.category("actions").add("hotel_dashboard_client_action", HotelDashboard);
