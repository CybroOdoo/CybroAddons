/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";

import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted, onWillUnmount } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';
import { user } from "@web/core/user";
import { browser } from "@web/core/browser/browser";
import { AiConfigModal }  from "./ai_config_modal";
import { AiLoadingModal } from "./ai_loading_modal";
import { DynamicDashboardCard } from './dynamic_dashboard_card';
/**
 * Loading status messages — cycle while AI is running.
 */
const MESSAGES = [
    "Thinking through your request",
    "Running inference…",
    "Almost there…",
    "Refining the details…",
    "Finalizing response structure…",
];
/**
 * Progress bar milestones: { p: percent, t: delay_ms }
 */
const PROGRESS_STEPS = [
    { p: 25,  t: 2000  },  // message 1
    { p: 50,  t: 5000  },  // message 2
    { p: 75,  t: 8000  },  // message 3
    { p: 95,  t: 11000 },  // message 4
    { p: 100, t: 14000 },  // message 4 → done
];

class DynamicDashboard extends Component {
    setup() {
        this.dashboardId = this.props.action.params?.dashboard_menu_id ||
            this.props.action.context?.dashboard_menu_id ||
            this.props.action.context?.params?.dashboard_menu_id ||
            parseInt(browser.sessionStorage.getItem('current_dashboard_menu_id'));


        if (this.dashboardId) {
            browser.sessionStorage.setItem('current_dashboard_menu_id', this.dashboardId);
        }

        this.nameInput = useRef("nameInput");
        this.gridRef = useRef("gridStackContainer");
        this.importCardInput = useRef("importCardInput");
        this.importDashboardInput = useRef("importDashboardInput");
        this.orm = useService('orm');
        this.action = useService("action");
        this.notification = useService("notification");
        this.ui = useService("ui");
        this.state = useState({
            data: {},
            dashboard: {},
            dashboards: {},
            dashboardName: "Dashboard",
            userName: user.name,
            editMode: false,
            adminNavBar: false,
            cards: [],
            grid: null,
            GridEditMode: false,
            slideshowMode: false,
            currentSlideIndex: 0,
            isAutoplay: false,
            activeFilter: 'all',
            activeFilterLabel: 'Date Filter',
            customStartDate: '',
            customEndDate: '',
            cyberpunkMode: false,
            darkMode: browser.localStorage.getItem('dashboard_dark_mode') === 'true',
            oceanBreezeMode: false,
            themes: [],
            theme_id: null,
            themeData: {},
            showThemeSubmenu: false,
            isLoading: false,
            progress:     0,
            loadingMsg:   MESSAGES[0],
            availableModels: [],
            showConfig: false,
        });
        onWillUnmount(() => this._clearTimers());
        /** Internal timer references — cleared on unmount. */
        this._timers = [];

        onWillStart(async () => {
            if (!this.dashboardId) {
                return;
            }
            this.state.dashboardName = this.props.action.params?.dashboard_name;
            this.state.availableModels = await this.orm.searchRead(
                "ir.model",
                [["transient", "=", false], ["abstract", "=", false]],
                ["model", "name"],
                { order: "name asc" }
            );

            // Get date filter from context if present
            const dateFilter = this.props.action.context?.dashboard_date_filter || 'all';
            if (dateFilter !== 'all') {
                this.state.activeFilter = dateFilter;
                const filterLabels = {
                    'today': 'Today',
                    'custom': 'Custom',
                };

                // Priority: Context label (for advanced filters) > Default labels > 'Date Filter'
                this.state.activeFilterLabel = this.props.action.context?.dashboard_date_label || filterLabels[dateFilter] || 'Date Filter';

                if (dateFilter === 'custom') {
                    // If it has a label from context, it's an advanced filter, not a manual custom one
                    if (this.props.action.context?.dashboard_date_label) {
                        this.state.activeFilter = 'advanced';
                    }
                    this.state.customStartDate = this.props.action.context?.dashboard_date_start || '';
                    this.state.customEndDate = this.props.action.context?.dashboard_date_end || '';
                }
            }

            this.adminUser = await user.hasGroup("odoo_dynamic_dashboard.group_dashboard_administrator");
            var dashboard = await this.orm.searchRead('dashboard.menu', [['id', '=', this.dashboardId]], [])
            this.state.dashboards = await this.orm.searchRead('dashboard.menu', [], ["id", "dashboard_name"])
            this.state.colorGroups = await this.orm.searchRead('dashboard.color.group', [], ["id", "name"])
            this.state.themes = await this.orm.searchRead('dashboard.theme.group', [['active', '=', true]], ["id", "name"])

            if (dashboard && dashboard.length > 0) {
                // Persisted dark-mode preference on the dashboard record wins over
                // the localStorage fallback used during initial state setup.
                if (dashboard[0].dark_mode_enabled !== undefined) {
                    this.state.darkMode = !!dashboard[0].dark_mode_enabled;
                    browser.localStorage.setItem('dashboard_dark_mode', this.state.darkMode);
                }
                // Fetch theme data
                if (dashboard[0].theme_id) {
                    this.state.theme_id = dashboard[0].theme_id[0];
                    const themeName = dashboard[0].theme_id[1];
                    // Visual mode classes only apply when dark mode is OFF —
                    // otherwise they'd stack with .dark-mode and combine styles.
                    this.state.oceanBreezeMode = !this.state.darkMode && themeName === 'Ocean Blue';
                    this.state.cyberpunkMode = !this.state.darkMode && themeName === 'Cyberpunk';

                    this.state.themeData = await this.orm.call('dashboard.menu', 'get_theme_data', [this.dashboardId]);
                    this.applyThemeColors();
                } else {
                    this.applyThemeColors();
                }
                // Fetch custom filters
                const customFilterIds = dashboard[0].custom_filter_ids;
                if (customFilterIds && customFilterIds.length > 0) {
                    this.state.customFilters = await this.orm.read('dashboard.custom.filter', customFilterIds, ['id', 'name', 'model_id', 'domain']);
                } else {
                    this.state.customFilters = [];
                }

                // Fetch advanced date filters
                const advancedFilterIds = dashboard[0].advanced_date_filter_ids;
                if (advancedFilterIds && advancedFilterIds.length > 0) {
                    this.state.advancedDateFilters = await this.orm.read('dashboard.date.filter', advancedFilterIds,
                        ['id', 'name', 'filter_type', 'year', 'month', 'week_number', 'day_range_start', 'day_range_end']);
                } else {
                    this.state.advancedDateFilters = [];
                }

                const backendFilterId = this.props.action.context?.dashboard_custom_filter_id;
                if (backendFilterId) {
                    const filter = this.state.customFilters.find(f => f.id == backendFilterId);
                    if (filter) {
                        this.state.activeCustomFilter = filter;
                        this.state.activeBackendFilter = filter;
                    }
                }


                this.state.dashboard = dashboard[0];

                this.state.dashboard = dashboard[0];

                // Fetch cards with date filter context
                this.state.cards = await this.orm.searchRead(
                    'dashboard.card',
                    [['dashboard_menu_id', '=', this.dashboardId]],
                    [
                        'id', 'name', 'description', 'type', 'gs_x', 'gs_y', 'gs_w', 'gs_h',
                        'background_color', 'chart_type', 'chart_x_axis_data', 'chart_y_axis_data',
                        'chart_color', 'semi_circular', 'index_axis', 'color_group_id',
                        'table_headers', 'table_rows', 'table_type', 'table_limit',
                        'record_limit', 'table_order', 'show_record_count', 'model_id',
                        'model_name', 'domain', 'view_type', 'activity_type', 'enable_click',
                        'todo_type', 'dashboard_menu_id', 'todo_ids', 'view_records',
                        'group_by_field_id', 'measure_field_id', 'table_field_line_ids',
                        'legend', 'legend_position', 'legend_alignment', 'legend_label_pointstyle',
                        'aggregation_method', 'group_by_2', 'size', 'block_value', 'block_aggregation_method',
                        'icon_class', 'icon_layout', 'icon_color', 'icon_size'
                    ],
                    {
                        context: {
                            dashboard_date_filter: dateFilter,
                            dashboard_date_start: this.props.action.context?.dashboard_date_start,
                            dashboard_date_end: this.props.action.context?.dashboard_date_end,
                            dashboard_custom_filter_id: backendFilterId ? parseInt(backendFilterId) : false,
                        }
                    }
                );
            } else {
            }
        });

        onMounted(() => {
            this.initGrid();
            const dashboard = this.state.cards.find(c => c.dashboard_menu_id[0] === this.props.action.params.dashboard_menu_id);
        });



    }
    async onClickDashboardSettings() {
        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'dashboard.menu',
            res_id: this.dashboardId,
            views: [[false, 'form']],
            target: 'new',
            context: {
                form_view_ref: "odoo_dynamic_dashboard.dashboard_menu_view_form",
            },
        }, {
            onClose: async () => {
                this.action.doAction("soft_reload")
            }
        });
    }

    onClickPrint() {
        window.print();
    }

    async onClickSendMail() {
        const dashboardName = this.state.dashboard.dashboard_name || 'Dashboard';
        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'mail.compose.message',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_model: 'dashboard.menu',
                default_res_ids: [this.dashboardId],
                default_subject: dashboardName,
                default_body: _t("Please find the dashboard link here."),
            },
        });
    }





    onClickPlay() {
        if (!this.state.cards || this.state.cards.length === 0) {
            this.notification.add("No cards to display.", { type: "warning" });
            return;
        }
        this.state.slideshowMode = true;
        this.state.currentSlideIndex = 0;
        this.state.isAutoplay = true;
        this.startAutoplay();
    }

    closeSlideshow() {
        this.state.slideshowMode = false;
        this.stopAutoplay();
    }

    nextSlide() {
        if (this.state.cards.length === 0) return;
        this.state.currentSlideIndex = (this.state.currentSlideIndex + 1) % this.state.cards.length;
    }

    prevSlide() {
        if (this.state.cards.length === 0) return;
        this.state.currentSlideIndex = (this.state.currentSlideIndex - 1 + this.state.cards.length) % this.state.cards.length;
    }

    toggleAutoplay() {
        this.state.isAutoplay = !this.state.isAutoplay;
        if (this.state.isAutoplay) {
            this.startAutoplay();
        } else {
            this.stopAutoplay();
        }
    }

    startAutoplay() {
        this.stopAutoplay();
        this.autoplayInterval = setInterval(() => {
            this.nextSlide();
        }, 5000);
    }

    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }

    applyFilter(filterType) {
        const filterLabels = {
            'today': 'Today',
            'custom': 'Custom',
            'all': 'Date Filter'
        };

        this.state.activeFilter = filterType;
        this.state.activeFilterLabel = filterLabels[filterType] || 'Date Filter';

        // For custom filter, we don't reload immediately, we wait for user to select dates and click Apply
        if (filterType === 'custom') {
            return;
        }

        // Reload dashboard with filter context
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'DynamicDashboard',
            params: {
                dashboard_menu_id: this.dashboardId,
                dashboard_name: this.state.dashboard.dashboard_name,
            },
            context: {
                dashboard_date_filter: filterType,
                dashboard_custom_filter_id: this.state.activeBackendFilter ? this.state.activeBackendFilter.id : false,
            },
        });
    }

    onStartDateChange(ev) {
        this.state.customStartDate = ev.target.value;
        if (this.state.customStartDate && this.state.customEndDate) {
            this.applyCustomFilter();
        }
    }

    onEndDateChange(ev) {
        this.state.customEndDate = ev.target.value;
        if (this.state.customStartDate && this.state.customEndDate) {
            this.applyCustomFilter();
        }
    }

    applyCustomFilter() {
        if (!this.state.customStartDate || !this.state.customEndDate) {
            this.notification.add("Please select both start and end dates.", { type: "warning" });
            return;
        }

        if (new Date(this.state.customStartDate) > new Date(this.state.customEndDate)) {
            this.notification.add("Start date cannot be greater than end date.", { type: "warning" });
            return;
        }

        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'DynamicDashboard',
            params: {
                dashboard_menu_id: this.dashboardId,
                dashboard_name: this.state.dashboard.dashboard_name,
            },
            context: {
                dashboard_date_filter: 'custom',
                dashboard_date_start: this.state.customStartDate,
                dashboard_date_end: this.state.customEndDate,
                dashboard_custom_filter_id: this.state.activeBackendFilter ? this.state.activeBackendFilter.id : false,
            },
        });
    }

    applyAdvancedFilter(filter) {
        if (!filter) return;

        let startDate, endDate;
        const year = filter.year || new Date().getFullYear();

        if (filter.filter_type === 'year') {
            startDate = `${year}-01-01`;
            endDate = `${year}-12-31`;
        } else if (filter.filter_type === 'month') {
            const month = parseInt(filter.month);
            startDate = `${year}-${String(month).padStart(2, '0')}-01`;
            const lastDay = new Date(year, month, 0).getDate();
            endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
        } else if (filter.filter_type === 'week') {
            const month = parseInt(filter.month);
            const startDayValue = filter.day_range_start;
            const endDayValue = filter.day_range_end;

            const lastDayOfMonth = new Date(year, month, 0).getDate();

            const finalStartDay = Math.min(startDayValue, lastDayOfMonth);
            const finalEndDay = Math.min(endDayValue, lastDayOfMonth);

            startDate = `${year}-${String(month).padStart(2, '0')}-${String(finalStartDay).padStart(2, '0')}`;
            endDate = `${year}-${String(month).padStart(2, '0')}-${String(finalEndDay).padStart(2, '0')}`;
        }

        if (startDate && endDate) {
            this.state.activeFilter = 'advanced';
            this.state.activeFilterLabel = filter.name;
            this.action.doAction({
                type: 'ir.actions.client',
                tag: 'DynamicDashboard',
                params: {
                    dashboard_menu_id: this.dashboardId,
                    dashboard_name: this.state.dashboard.dashboard_name,
                },
                context: {
                    dashboard_date_filter: 'custom',
                    dashboard_date_start: startDate,
                    dashboard_date_end: endDate,
                    dashboard_date_label: filter.name,
                    dashboard_custom_filter_id: this.state.activeBackendFilter ? this.state.activeBackendFilter.id : false,
                },
            });
        }
    }

    applyBackendCustomFilter(filter) {
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'DynamicDashboard',
            params: {
                dashboard_menu_id: this.dashboardId,
                dashboard_name: this.state.dashboard.dashboard_name,
            },
            context: {
                dashboard_date_filter: this.state.activeFilter,
                dashboard_date_start: this.state.customStartDate,
                dashboard_date_end: this.state.customEndDate,
                dashboard_custom_filter_id: filter ? filter.id : false,
            },
        });
    }






    async toggleDarkMode(ev) {
        this.state.darkMode = ev.target.checked;
        if (this.state.darkMode) {
            // Dark mode owns the appearance — disable special visual themes
            // so their CSS classes don't stack and combine styles with dark.
            this.state.oceanBreezeMode = false;
            this.state.cyberpunkMode = false;
        } else {
            // Going back to light: re-apply the selected theme's visual mode.
            const theme = this.state.themes.find(t => t.id === this.state.theme_id);
            const themeName = theme ? theme.name : '';
            this.state.oceanBreezeMode = themeName === 'Ocean Blue';
            this.state.cyberpunkMode = themeName === 'Cyberpunk';
        }
        browser.localStorage.setItem('dashboard_dark_mode', this.state.darkMode);
        this.applyThemeColors();
        // Persist the user's choice on the dashboard record so it's restored on next load.
        if (this.dashboardId) {
            try {
                await this.orm.write('dashboard.menu', [this.dashboardId], {
                    dark_mode_enabled: this.state.darkMode,
                });
            } catch (e) {
                // Pre-upgrade DBs may lack the field; silently fall back to localStorage only.
            }
        }
    }




    initGrid() {
        // Initialize GridStack only once
        if (!this.state.grid && this.gridRef.el) {
            const grid = GridStack.init(
                {
                    float: true,
                    // Set margin/spacing between grid items (in pixels)
                    margin: 10,
                    // Add responsive column options with breakpoints
                    columnOpts: {
                        breakpoints: [
                            { w: 1200, c: 12 },
                            { w: 992, c: 9 },
                            { w: 768, c: 6 },
                            { w: 576, c: 1 }
                        ],
                        // Specify if breakpoints are for window size (true) or grid size (false)
                        breakpointForWindow: false,  // Default: false (grid size)
                        // Maximum columns allowed (ensure CSS supports this)
                        columnMax: 12,
                        // Layout behavior when columns change
                        layout: 'moveScale'  // Options: 'moveScale', 'move', 'scale', 'list', 'compact', 'none'
                    },
                    // Show resize handles on mobile
                    alwaysShowResizeHandle: 'mobile',
                    // Cell height configuration
                    cellHeight: 'auto',  // Makes cells square based on width
                },
                this.gridRef.el
            );

            if (grid) {
                // Disable interactivity initially (read-only mode)
                grid.enableMove(false);
                grid.enableResize(false);

                this.grid = grid;
            }
        }
    }
    cancelChanges() {
        this.state.GridEditMode = false;
        this.action.doAction("soft_reload");

    }
    onImportCard() {
        if (this.importCardInput.el) {
            this.importCardInput.el.click();
        }
    }

    async onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const cardData = JSON.parse(e.target.result);

                // Sanitize and set dashboard_menu_id
                delete cardData.id;
                cardData.dashboard_menu_id = this.dashboardId;

                // Reset position if it was exported from a different dashboard layout
                // or just keep it at 0,0 for now to avoid overlapping
                cardData.gs_x = 0;
                cardData.gs_y = 0;

                await this.orm.create('dashboard.card', [cardData]);

                this.notification.add(_t("Card imported successfully"), {
                    type: "success",
                });

                // Reload dashboard
                window.location.reload();
            } catch (err) {
                this.notification.add(_t("Failed to import card: Invalid JSON format"), {
                    type: "danger",
                });
            } finally {
                // Clear input
                ev.target.value = '';
            }
        };
        reader.readAsText(file);
    }

    async onClickExportDashboard() {
        try {
            const cardsToExport = await this.orm.call("dashboard.menu", "export_dashboard", [this.dashboardId]);

            if (!cardsToExport || cardsToExport.length === 0) {
                this.notification.add(_t("No cards to export."), { type: "warning" });
                return;
            }

            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(cardsToExport, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", (this.state.dashboardName || "dashboard") + "_export.json");
            document.body.appendChild(downloadAnchorNode); // required for firefox
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        } catch (e) {
            this.notification.add(_t("Export failed: " + e.message), { type: "danger" });
        }
    }

    onClickImportDashboard() {
        if (this.importDashboardInput.el) {
            this.importDashboardInput.el.click();
        }
    }

    async onDashboardFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const importedCards = JSON.parse(e.target.result);
                if (!Array.isArray(importedCards)) {
                    throw new Error("Invalid format: Expected an array of cards.");
                }

                await this.orm.call("dashboard.menu", "import_dashboard", [this.dashboardId, importedCards]);

                this.notification.add(_t("Dashboard imported successfully"), {
                    type: "success",
                });

                // Reload dashboard
                window.location.reload();
            } catch (err) {
                this.notification.add(_t("Failed to import dashboard: " + err.message), {
                    type: "danger",
                });
            } finally {
                ev.target.value = '';
            }
        };
        reader.readAsText(file);
    }

    OnClickEdit() {
        if (this.grid) {
            this.originalLayout = this.grid.save()
            this.grid.enableMove(true);
            this.grid.enableResize(true);
            this.grid.float(true);
            this.state.GridEditMode = true;
        }
    }
    toggleEditMode() {
        this.state.editMode = !this.state.editMode;
        if (!this.state.editMode) {
            // If exiting edit mode without saving, revert name
            this.state.dashboardName = this.state.dashboardName; // Revert to original or last saved name
        }
    }
    async OnClickSave() {
        const root = this.gridRef.el;
        const items = root.querySelectorAll(".o_dynamic_dashboard_grid_item");
        for (const el of items) {
            await this.orm.write("dashboard.card", [parseInt(el.getAttribute('id'))], {
                gs_x: parseInt(el.getAttribute('gs-x')) || 0,
                gs_y: parseInt(el.getAttribute('gs-y')) || 0,
                gs_h: parseInt(el.getAttribute('gs-h')) || 2,
                gs_w: parseInt(el.getAttribute('gs-w')) || 3,
            });
        }
        this.grid.enableMove(false);
        this.grid.enableResize(false);
        this.state.GridEditMode = false;
        this.action.doAction("soft_reload");
    }

    /**
     * Auto-arrange cards using a 2D bin-packing pass (first-fit decreasing).
     * Sorts cards by area (largest first) and places each one at the topmost-
     * leftmost free position that fits, maximising horizontal space usage and
     * eliminating gaps between rows.
     */
    async onFormatLayout() {
        if (!this.grid) return;

        const COLS = this.grid.getColumn() || 12;
        const nodes = (this.grid.engine && this.grid.engine.nodes)
            ? this.grid.engine.nodes.slice()
            : [];
        if (nodes.length === 0) return;

        // Sort: largest area first, taller items as a tie-breaker. Packs big
        // blocks first then fills the remaining gaps with smaller cards.
        nodes.sort((a, b) => {
            const areaDiff = (b.w * b.h) - (a.w * a.h);
            return areaDiff !== 0 ? areaDiff : (b.h - a.h);
        });

        // Sparse occupancy grid keyed by "x,y".
        const occupied = new Set();
        const isFree = (x, y, w, h) => {
            if (x < 0 || x + w > COLS) return false;
            for (let dy = 0; dy < h; dy++) {
                for (let dx = 0; dx < w; dx++) {
                    if (occupied.has(`${x + dx},${y + dy}`)) return false;
                }
            }
            return true;
        };
        const occupy = (x, y, w, h) => {
            for (let dy = 0; dy < h; dy++) {
                for (let dx = 0; dx < w; dx++) {
                    occupied.add(`${x + dx},${y + dy}`);
                }
            }
        };

        // First-fit scan: top-to-bottom rows, left-to-right per row.
        const MAX_ROWS = 500;
        const placements = [];
        for (const node of nodes) {
            const w = Math.min(node.w || 1, COLS);
            const h = Math.max(node.h || 1, 1);
            let placed = false;
            for (let y = 0; !placed && y < MAX_ROWS; y++) {
                for (let x = 0; x <= COLS - w; x++) {
                    if (isFree(x, y, w, h)) {
                        occupy(x, y, w, h);
                        placements.push({ node, x, y, w, h });
                        placed = true;
                        break;
                    }
                }
            }
        }

        // GridStack ignores update() when move/resize are disabled, so
        // temporarily enable them, apply the new layout, then restore.
        const wasInEditMode = this.state.GridEditMode;
        this.grid.enableMove(true);
        this.grid.enableResize(true);
        this.grid.float(false); // disable float so cards pack upward
        this.grid.batchUpdate();
        for (const { node, x, y, w, h } of placements) {
            this.grid.update(node.el, { x, y, w, h });
        }
        this.grid.commit();
        if (!wasInEditMode) {
            this.grid.enableMove(false);
            this.grid.enableResize(false);
        }
        this.grid.float(true);  // restore default float behavior

        // Persist new positions on the dashboard.card records.
        for (const { node, x, y, w, h } of placements) {
            const cardId = parseInt(node.el.getAttribute('id'));
            if (!cardId) continue;
            await this.orm.write('dashboard.card', [cardId], {
                gs_x: x, gs_y: y, gs_w: w, gs_h: h,
            });
        }
        this.notification.add(_t("Layout formatted"), { type: "success" });
    }

    onClickAdminNav() {
        this.state.adminNavBar = !this.state.adminNavBar;
    }
    async saveName() {
        this.state.dashboard.dashboard_name = this.nameInput.el.value;
        await this.orm.write('dashboard.menu', [this.state.dashboard.id], { dashboard_name: this.nameInput.el.value })
        this.state.editMode = false;
        // In a real scenario, you would save this.state.dashboardName to the backend
    }

    cancelEdit() {
        this.state.editMode = false;
        this.state.dashboardName = this.state.dashboardName
    }
    showLoading() {
        this.state.isLoading = true;
        this.state.progress  = 0;
    }
     hideLoading() {
        this.state.isLoading = false;
        this.state.progress  = 0;
    }
    async onClickCreateBlockAI(){
    if (this.state.isLoading) return;
        this.state.showConfig = true;
    }
    async onConfigConfirm({ model, maxCards }) {
        this.state.showConfig = false;
        await this._startLoading(model, maxCards);
        this.action.doAction("soft_reload")
    }

    async _startLoading(model, maxCards){
        this._clearTimers();
        this.state.isLoading  = true;
        this.state.progress   = 0;
        this.state.loadingMsg = MESSAGES[0];

        // Step progress bar + message in sync
        PROGRESS_STEPS.forEach(({ p, t }, idx) => {
            const id = setTimeout(() => {
                this.state.progress   = p;
                this.state.loadingMsg = MESSAGES[Math.min(idx + 1, MESSAGES.length - 1)];
            }, t);
            this._timers.push(id);
        });
         var newCards = await this.orm.call(
                "dashboard.card",
                "generate_max_cards_from_model",
                [model], // Positional arguments
                {
                    // Keyword arguments
                    dashboard_menu_id: this.dashboardId,
                    max_cards: maxCards
                }
            );
        if(newCards == 'success'){
            this._finishLoading()
            this.notification.add(_t("Cards created successfully"), {
                    type: "success",
                });
        }
    }
    _finishLoading() {
        this._clearTimers();
        this.state.isLoading  = false;
        this.state.progress   = 0;
    }

    onConfigCancel() {
        this.state.showConfig = false;
    }
    _clearTimers() {
        this._timers.forEach((id) => { clearTimeout(id); clearInterval(id); });
        this._timers = [];
    }
    async onClickCreateBlock() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Create Card Block",
            res_model: "dashboard.card",
            views: [[false, "form"]],
            context: {
                default_dashboard_menu_id: this.dashboardId,
                form_view_ref: "odoo_dynamic_dashboard.dashboard_card_view_form_wizard",
            },
            target: "new", // 'new' opens in dialog, 'current' replaces the current view
        },
            {
                onClose: async () => {
                    this.action.doAction("soft_reload")
                },
            })
    }
    async onClickDuplicateDashboard() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Duplicate Dashboard",
            res_model: "dashboard.duplicate.wizard",
            views: [[false, "form"]],
            target: "new",
            context: {
                active_id: this.dashboardId,
            }
        });
    }

    onThemeClick(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.state.showThemeSubmenu = !this.state.showThemeSubmenu;
    }

    async selectTheme(themeId) {
        await this.orm.write('dashboard.menu', [this.dashboardId], {
            theme_id: themeId
        });
        this.state.theme_id = themeId;
        const theme = this.state.themes.find(t => t.id === themeId);
        if (theme) {
            this.state.darkMode = theme.name === 'Dark';
            this.state.oceanBreezeMode = theme.name === 'Ocean Blue';
            this.state.cyberpunkMode = theme.name === 'Cyberpunk';
        }
        this.state.themeData = await this.orm.call('dashboard.menu', 'get_theme_data', [this.dashboardId]);
        this.applyThemeColors();
        this.notification.add(_t("Theme updated successfully"), { type: "success" });
    }

    applyThemeColors() {
        const root = document.documentElement;
        const SCOPED_ID = 'ad_dashboard_theme_overrides';

        // === DARK MODE: take this branch FIRST and never mix in theme values.
        if (this.state.darkMode) {
            // Fixed dark palette — ignore whatever theme is selected.
            root.style.setProperty('--dashboard-bg', '#1a1d21');
            root.style.setProperty('--card-bg', '#262a32', 'important');
            root.style.setProperty('--main-text', '#f8fafc');
            root.style.setProperty('--navbar-bg', '#262a32');
            root.style.setProperty('--sidebar-toggle', '#4b5563');
            root.style.setProperty('--dashboard-card-bg', '#1e1e1e');
            root.style.removeProperty('--card-text');
            // Clear any light-mode scoped overrides so the dark-mode CSS wins.
            const scopedStyle = document.getElementById(SCOPED_ID);
            if (scopedStyle) scopedStyle.textContent = '';
            // Scrollbar colours for dark mode.
            const darkScroll = '#4b5563';
            root.style.setProperty('--scrollbar-thumb-color', darkScroll);
            root.style.setProperty('--scrollbar-track-color', darkScroll + '20');
            root.style.setProperty('--scrollbar-thumb-hover-color', darkScroll);
            return;
        }

        // === LIGHT MODE: drive everything from theme data, with safe defaults.
        const data = this.state.themeData || {};
        const bgColor = data.background_color || '#f8f9fa';
        const cardColor = data.card_background_color || '#ffffff';
        const textColor = data.text_color || '#1a1a1a';
        const cardTextColor = data.card_text_color || '#1a1a1a';
        const dashCardColor = data.dashboard_card_color || '#ffffff';
        const navBarColor = data.navbar_color || '#ffffff';
        const sidebarColor = data.sidebar_toggle_color || '#71639e';

        root.style.setProperty('--dashboard-bg', bgColor);
        root.style.setProperty('--card-bg', cardColor, 'important');
        root.style.setProperty('--main-text', textColor);
        root.style.setProperty('--navbar-bg', navBarColor);
        root.style.setProperty('--sidebar-toggle', sidebarColor);
        root.style.setProperty('--dashboard-card-bg', dashCardColor);
        root.style.setProperty('--card-text', cardTextColor, 'important');
        if (data.button_color) root.style.setProperty('--primary-btn', data.button_color);

        // Scoped <style> tag with hardcoded hex values — bulletproof override
        // for every card surface in light mode.
        let scopedStyle = document.getElementById(SCOPED_ID);
        if (!scopedStyle) {
            scopedStyle = document.createElement('style');
            scopedStyle.id = SCOPED_ID;
            document.head.appendChild(scopedStyle);
        }
        scopedStyle.textContent = `
            .ad_dashboard:not(.dark-mode) .card,
            .ad_dashboard:not(.dark-mode) .grid-stack-item-content,
            .ad_dashboard:not(.dark-mode) .card.h-100 {
                background-color: ${cardColor} !important;
                background: ${cardColor} !important;
            }
            /* Inner card containers transparent so the themed card bg shows
               through for ALL card types (chart, table, activity, todo, view). */
            .ad_dashboard:not(.dark-mode) .card .card-body,
            .ad_dashboard:not(.dark-mode) .dashboard-chart-component,
            .ad_dashboard:not(.dark-mode) .dashboard-table-component,
            .ad_dashboard:not(.dark-mode) .activity-container,
            .ad_dashboard:not(.dark-mode) .todo-container {
                background-color: transparent !important;
                background: transparent !important;
            }
            .ad_dashboard:not(.dark-mode) .tile-value,
            .ad_dashboard:not(.dark-mode) .tile-label,
            .ad_dashboard:not(.dark-mode) .tile-subtext {
                color: ${cardTextColor} !important;
            }
            /* Empty-state ("No record" / "No data") surfaces also use the
               themed card bg so they blend into the card. */
            .ad_dashboard:not(.dark-mode) .table-empty-state,
            .ad_dashboard:not(.dark-mode) .view-empty-state,
            .ad_dashboard:not(.dark-mode) .chart-empty-state,
            .ad_dashboard:not(.dark-mode) .todo-empty-state,
            .ad_dashboard:not(.dark-mode) .o_dashboard_empty_state {
                background: ${cardColor} !important;
                background-color: ${cardColor} !important;
                color: ${cardTextColor} !important;
            }
        `;

        // Scrollbar colours follow the theme accent.
        const scrollColor = data.sidebar_toggle_color || '#71639e';
        root.style.setProperty('--scrollbar-thumb-color', scrollColor);
        root.style.setProperty('--scrollbar-track-color', scrollColor + '20');
        root.style.setProperty('--scrollbar-thumb-hover-color', scrollColor);

        if (data.card_spacing) {
            root.style.setProperty('--card-margin', `${data.card_spacing}px`);
        }

        // Background Logic: Image > Gradient > Solid Color
        if (data.background_image) {
            const imageUrl = `/web/image/dashboard.theme.group/${data.id}/background_image`;

            // Determine background size
            let bgSize = 'cover'; // Default
            if (data.background_size === 'contain') bgSize = 'contain';
            if (data.background_size === 'stretch') bgSize = '100% 100%';
            if (data.background_size === 'auto') bgSize = 'auto';

            // If Gradient is also enabled, overlay it on the image
            if (data.is_gradient && data.gradient_color_1 && data.gradient_color_2 && !this.state.darkMode) {
                // Ensure colors have transparency for overlay if they are Hex
                let col1 = data.gradient_color_1;
                let col2 = data.gradient_color_2;

                // Simple check to add transparency to Hex colors to allow image to show through
                if (col1.startsWith('#') && col1.length === 7) col1 += 'CC'; // ~80% opacity
                if (col2.startsWith('#') && col2.length === 7) col2 += 'CC';

                const gradient = `linear-gradient(${data.gradient_degree || 90}deg, ${col1}, ${col2})`;

                // Apply Gradient ON TOP of Image
                root.style.setProperty('--dashboard-bg',
                    `${gradient}, url('${imageUrl}') no-repeat fixed center / ${bgSize}`
                );
            } else {
                // Image Only
                root.style.setProperty('--dashboard-bg', `url('${imageUrl}') no-repeat fixed center / ${bgSize}`);
            }
        }
        // Fallback to Gradient Only (No Image)
        else if (!this.state.darkMode && data.is_gradient && data.gradient_color_1 && data.gradient_color_2) {
            const gradient = `linear-gradient(${data.gradient_degree || 90}deg, ${data.gradient_color_1}, ${data.gradient_color_2})`;
            root.style.setProperty('--dashboard-bg', gradient);
        }
    }

}

DynamicDashboard.template = 'DynamicDashboardTemplate';
DynamicDashboard.components = { DynamicDashboardCard, AiLoadingModal, AiConfigModal };
registry.category('actions').add('DynamicDashboard', DynamicDashboard);
