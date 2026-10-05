import { browser } from "@web/core/browser/browser";
import { formatDateTime } from "@web/core/l10n/dates";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { useSortable } from "@web/core/utils/sortable_owl";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { Component, onMounted, onWillStart, onWillUnmount, proxy, signal, useProps } from "@odoo/owl";
import {
    BLOCK_COLORS,
    autoArrangeBlocks,
    createBlock,
    getBlockConfig,
    getBlockIssue,
    prepareBlock,
} from "../block_catalog/block_catalog";
import { BlockAiAnalysisDialog } from "../ai_analysis/ai_analysis_dialog";
import { DashboardAiDialog } from "../ai_dialog/ai_dialog";
import {
    BlockFilterPanel,
    buildFilterDomain,
    countActiveFilters,
    emptyFilter,
    getFilterSummary,
} from "../block_filter/block_filter";
import { BlockConfigurator } from "../block_configurator/block_configurator";
import { BLOCK_DRAG_TYPE, BlockPalette } from "../block_palette/block_palette";
import { DashboardBlock } from "../dashboard_block/dashboard_block";
import { DashboardMenuDialog } from "../menu_dialog/menu_dialog";
import { DashboardPresentation } from "../presentation/presentation";

const DASHBOARD_MODEL = "dynamic.dashboard";
const BLOCK_MODEL = "dynamic.dashboard.block";
const MANAGER_GROUP = "odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_manager";
const LAST_DASHBOARD_KEY = "odoo_dynamic_dashboard.last_dashboard_id";
const FILTERS_KEY = "odoo_dynamic_dashboard.filters";
const PREVIEW_DELAY = 300;
// values computed by the server for a block, refreshed by each preview
const COMPUTED_KEYS = [
    "measure_label", "error", "value", "labels", "label_domains", "series", "columns", "rows", "record_domain",
];

/**
 * Dashboard client action. It displays a dashboard and, in edit mode, is the dashboard
 * builder: blocks are dragged from the palette, configured in the side panel with a
 * live preview, arranged, and the whole dashboard is saved at once.
 *
 * Action params:
 * - ``dashboard_id``: the dashboard to open (set on the menu items of dashboards)
 * - ``new_dashboard``: open the builder on a new dashboard
 * - ``generate_with_ai``: with ``new_dashboard``, open the AI generator right away
 */
export class DynamicDashboardAction extends Component {
    static template = "odoo_dynamic_dashboard.DashboardAction";
    static components = {
        BlockConfigurator,
        BlockFilterPanel,
        BlockPalette,
        ControlPanel,
        DashboardBlock,
        DashboardPresentation,
        Dropdown,
        DropdownItem,
    };

    props = useProps(standardActionServiceProps);

    gridRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.menuService = useService("menu");
        this.notification = useService("notification");
        const params = this.props.action.params || {};
        this.isDedicated = Boolean(params.dashboard_id);
        this.state = proxy({
            dashboards: [],
            dashboard: null,
            editMode: false,
            isDirty: false,
            isLoading: false,
            isSaving: false,
            canManageMenu: false,
            selectedUid: null,
            // index at which the block dragged from the palette would be inserted
            dropIndex: null,
            isPresenting: false,
            // block whose viewer filters are edited in the side panel
            filterUid: null,
            printDate: "",
        });
        this.previewTimers = new Map();

        useSortable({
            ref: this.gridRef,
            enable: () => this.state.editMode,
            elements: ".o_dynamic_dashboard_cell",
            handle: ".o_dynamic_dashboard_block_handle",
            cursor: "move",
            onDrop: ({ element, previous }) => this.moveBlock(element, previous),
        });

        onWillStart(async () => {
            this.state.canManageMenu = await user.hasGroup(MANAGER_GROUP);
            if (params.new_dashboard) {
                this.startNewDashboard();
                return;
            }
            await this.loadDashboardList();
            const dashboardId =
                params.dashboard_id ||
                parseInt(browser.localStorage.getItem(LAST_DASHBOARD_KEY), 10) ||
                false;
            await this.loadDashboard(dashboardId);
        });
        onMounted(() => {
            if (params.new_dashboard && params.generate_with_ai) {
                this.openAiDialog();
            }
        });
        onWillUnmount(() => {
            for (const timer of this.previewTimers.values()) {
                browser.clearTimeout(timer);
            }
        });
    }

    // Loading ------------------------------------------------------------------

    async loadDashboardList() {
        this.state.dashboards = await this.orm.call(DASHBOARD_MODEL, "get_dashboard_list", []);
    }

    async loadDashboard(dashboardId) {
        const ids = this.state.dashboards.map((dashboard) => dashboard.id);
        if (!ids.includes(dashboardId)) {
            dashboardId = this.isDedicated ? false : ids[0];
        }
        if (!dashboardId) {
            this.state.dashboard = null;
            return;
        }
        this.state.isLoading = true;
        try {
            const dashboard = await this.orm.call(DASHBOARD_MODEL, "get_dashboard_data", [[dashboardId]]);
            this.setDashboard(dashboard);
        } finally {
            this.state.isLoading = false;
        }
        browser.localStorage.setItem(LAST_DASHBOARD_KEY, dashboardId);
    }

    setDashboard(dashboard) {
        this.state.dashboard = {
            ...dashboard,
            blocks: dashboard.blocks.map((block) => prepareBlock(block)),
        };
        this.state.selectedUid = null;
        this.state.filterUid = null;
        this.state.isDirty = false;
        this.restoreFilters();
    }

    async reload() {
        await this.loadDashboard(this.state.dashboard?.id);
    }

    startNewDashboard() {
        this.state.dashboard = {
            id: false,
            name: "",
            can_edit: true,
            menu_id: false,
            menu_name: "",
            menu_parent_id: false,
            blocks: [],
        };
        this.state.editMode = true;
        this.state.isDirty = false;
        this.state.selectedUid = null;
    }

    // Builder ------------------------------------------------------------------

    getSelectedBlock() {
        return this.state.dashboard?.blocks.find((block) => block.uid === this.state.selectedUid);
    }

    enterEditMode() {
        this.state.editMode = true;
        this.state.filterUid = null;
    }

    selectBlock(block) {
        this.state.selectedUid = block?.uid ?? null;
    }

    onNameInput(ev) {
        this.state.dashboard.name = ev.target.value;
        this.state.isDirty = true;
    }

    addBlock(blockType, index = null) {
        const blocks = this.state.dashboard.blocks;
        const block = createBlock(blockType, { color: BLOCK_COLORS[blocks.length % BLOCK_COLORS.length] });
        blocks.splice(index ?? blocks.length, 0, block);
        this.state.isDirty = true;
        this.selectBlock(block);
    }

    duplicateBlock(block) {
        const blocks = this.state.dashboard.blocks;
        const copy = prepareBlock({ ...block, id: false }, { customName: block.customName });
        blocks.splice(blocks.indexOf(block) + 1, 0, copy);
        this.state.isDirty = true;
        this.selectBlock(copy);
    }

    removeBlock(block) {
        const blocks = this.state.dashboard.blocks;
        blocks.splice(blocks.indexOf(block), 1);
        if (this.state.selectedUid === block.uid) {
            this.selectBlock(null);
        }
        this.state.isDirty = true;
    }

    updateBlock(block, changes) {
        Object.assign(block, changes);
        this.state.isDirty = true;
        const keys = Object.keys(changes);
        if (keys.length === 1 && keys[0] === "width") {
            return;
        }
        if (keys.every((key) => ["name", "customName"].includes(key)) && block.customName) {
            return;
        }
        this.schedulePreview(block);
    }

    schedulePreview(block) {
        browser.clearTimeout(this.previewTimers.get(block.uid));
        this.previewTimers.set(
            block.uid,
            browser.setTimeout(() => this.refreshPreview(block), PREVIEW_DELAY)
        );
    }

    async refreshPreview(block) {
        this.previewTimers.delete(block.uid);
        const requestId = (block.previewRequestId || 0) + 1;
        block.previewRequestId = requestId;
        const data = await this.orm.call(BLOCK_MODEL, "preview_block", [getBlockConfig(block)]);
        if (block.previewRequestId !== requestId) {
            return; // a more recent preview is on its way
        }
        this.applyBlockData(block, data);
        if (!block.customName) {
            block.name = data.name;
        }
    }

    applyBlockData(block, data) {
        for (const key of COMPUTED_KEYS) {
            delete block[key];
        }
        for (const key of COMPUTED_KEYS) {
            if (key in data) {
                block[key] = data[key];
            }
        }
        block.version++;
    }

    // AI ---------------------------------------------------------------------

    openAiDialog() {
        this.dialogService.add(DashboardAiDialog, {
            hasBlocks: Boolean(this.state.dashboard.blocks.length),
            onGenerated: (design, options) => this.applyAiDesign(design, options),
        });
    }

    /**
     * Add the blocks designed by the AI to the builder, as unsaved blocks the user
     * reviews before saving the dashboard.
     */
    applyAiDesign(design, { replace = false, blockCount = false } = {}) {
        const { dashboard } = this.state;
        if (!dashboard.name.trim() || (replace && !dashboard.id)) {
            dashboard.name = design.name;
        }
        const blocks = design.blocks.map((config) =>
            Object.assign(createBlock(config.block_type), config, { id: false, customName: true })
        );
        dashboard.blocks = autoArrangeBlocks([...(replace ? [] : dashboard.blocks), ...blocks]);
        this.state.isDirty = true;
        this.selectBlock(null);
        for (const block of dashboard.blocks.filter((block) => blocks.some((b) => b.uid === block.uid))) {
            this.refreshPreview(block);
        }
        if (blockCount && blocks.length < blockCount) {
            this.notification.add(
                _t(
                    "The AI designed %(count)s of the %(requested)s blocks asked: it did not find enough relevant data. Review them, then save.",
                    { count: blocks.length, requested: blockCount }
                ),
                { type: "warning" }
            );
            return;
        }
        this.notification.add(
            _t("The AI designed %s blocks. Review them, adjust them if needed, then save.", blocks.length),
            { type: "success" }
        );
    }

    generateDashboardWithAi() {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "odoo_dynamic_dashboard.dashboard",
            name: _t("New Dashboard"),
            params: { new_dashboard: true, generate_with_ai: true },
        });
    }

    autoArrange() {
        const { dashboard } = this.state;
        dashboard.blocks = autoArrangeBlocks([...dashboard.blocks]);
        this.state.isDirty = true;
    }

    moveBlock(element, previous) {
        const blocks = this.state.dashboard.blocks;
        const fromIndex = parseInt(element.dataset.index, 10);
        let toIndex = previous ? parseInt(previous.dataset.index, 10) + 1 : 0;
        if (fromIndex < toIndex) {
            toIndex--;
        }
        if (fromIndex === toIndex) {
            return;
        }
        const [block] = blocks.splice(fromIndex, 1);
        blocks.splice(toIndex, 0, block);
        this.state.isDirty = true;
    }

    async save() {
        const { dashboard } = this.state;
        if (!dashboard.name.trim()) {
            this.notification.add(_t("Give a name to your dashboard."), { type: "danger" });
            document.querySelector(".o_dynamic_dashboard_name_input")?.focus();
            return;
        }
        const incompleteBlock = dashboard.blocks.find((block) => getBlockIssue(block));
        if (incompleteBlock) {
            this.selectBlock(incompleteBlock);
            this.notification.add(
                _t("Finish configuring the block “%s”, or remove it.", incompleteBlock.name),
                { type: "warning" }
            );
            return;
        }
        const isNew = !dashboard.id;
        this.state.isSaving = true;
        let result;
        try {
            result = await this.orm.call(DASHBOARD_MODEL, "save_from_builder", [
                {
                    id: dashboard.id,
                    name: dashboard.name.trim(),
                    blocks: dashboard.blocks.map((block) => ({ ...getBlockConfig(block), name: block.name })),
                },
            ]);
        } finally {
            this.state.isSaving = false;
        }
        this.setDashboard(result);
        this.state.editMode = false;
        browser.localStorage.setItem(LAST_DASHBOARD_KEY, result.id);
        this.env.config.setDisplayName?.(result.name);
        await this.loadDashboardList();
        if (!result.menu_id && this.state.canManageMenu) {
            this.openMenuDialog();
        } else if (isNew && !this.state.canManageMenu) {
            this.notification.add(
                _t("Dashboard saved. Ask a dashboard administrator to add it to a menu."),
                { type: "success" }
            );
        } else {
            this.notification.add(_t("Dashboard saved."), { type: "success" });
        }
    }

    discard() {
        const leave = () => {
            if (this.state.dashboard.id) {
                this.state.editMode = false;
                this.reload();
            } else {
                this.leaveBuilder();
            }
        };
        if (!this.state.isDirty) {
            leave();
            return;
        }
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Discard Changes"),
            body: _t("Your changes to this dashboard will be lost."),
            confirmLabel: _t("Discard"),
            confirmClass: "btn-danger",
            confirm: leave,
            cancel: () => {},
        });
    }

    leaveBuilder() {
        if ((this.env.config.breadcrumbs?.length || 0) > 1) {
            this.actionService.restore();
        } else {
            this.actionService.doAction("odoo_dynamic_dashboard.dynamic_dashboard_action_client", {
                clearBreadcrumbs: true,
            });
        }
    }

    // Menu ---------------------------------------------------------------------

    openMenuDialog() {
        const { dashboard } = this.state;
        this.dialogService.add(DashboardMenuDialog, {
            menuName: dashboard.menu_name || dashboard.name,
            parentMenuId: dashboard.menu_parent_id || false,
            isUpdate: Boolean(dashboard.menu_id),
            onConfirm: async ({ menuName, parentMenuId }) => {
                const menuId = await this.orm.call(DASHBOARD_MODEL, "set_dashboard_menu", [
                    [dashboard.id],
                    menuName,
                    parentMenuId,
                ]);
                await this.menuService.reload();
                this.notification.add(_t("The dashboard is now in the menu “%s”.", menuName), {
                    type: "success",
                });
                // open the dashboard from its own menu item
                await this.menuService.selectMenu(menuId);
            },
        });
    }

    // Dashboards ---------------------------------------------------------------

    createDashboard() {
        this.actionService.doAction("odoo_dynamic_dashboard.dynamic_dashboard_action_builder");
    }

    deleteDashboard() {
        const { id, name, menu_id: menuId } = this.state.dashboard;
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Delete Dashboard"),
            body: _t('Are you sure you want to delete the dashboard "%s" and all its blocks?', name),
            confirmLabel: _t("Delete"),
            confirmClass: "btn-danger",
            confirm: async () => {
                await this.orm.unlink(DASHBOARD_MODEL, [id]);
                if (menuId) {
                    await this.menuService.reload();
                }
                this.state.editMode = false;
                if (this.isDedicated) {
                    this.leaveBuilder();
                    return;
                }
                await this.loadDashboardList();
                await this.loadDashboard(false);
            },
            cancel: () => {},
        });
    }

    // Viewer filters -----------------------------------------------------------

    /**
     * Each block can be filtered by its viewer (period, values, conditions). The
     * filters are personal: they are kept in the browser, not in the dashboard.
     */
    readStoredFilters() {
        try {
            return JSON.parse(browser.localStorage.getItem(FILTERS_KEY) || "{}");
        } catch {
            return {};
        }
    }

    storeFilters() {
        const { dashboard } = this.state;
        const stored = this.readStoredFilters();
        stored[dashboard.id] = Object.fromEntries(
            dashboard.blocks
                .filter((block) => block.id && countActiveFilters(block.filter))
                .map((block) => [block.id, block.filter])
        );
        try {
            browser.localStorage.setItem(FILTERS_KEY, JSON.stringify(stored));
        } catch {
            // storage full or disabled: the filters only last for this visit
        }
    }

    restoreFilters() {
        const { dashboard } = this.state;
        const stored = (dashboard.id && this.readStoredFilters()[dashboard.id]) || {};
        for (const block of dashboard.blocks) {
            // the values a block can be narrowed to, taken from its unfiltered data
            block.filterOptions = (block.labels || []).map((label, index) => ({
                label,
                domain: block.label_domains?.[index] || [],
            }));
            if (countActiveFilters(stored[block.id])) {
                block.filter = { ...emptyFilter(), ...stored[block.id] };
                this.refreshFilteredBlock(block);
            }
        }
    }

    getFilterCount(block) {
        return countActiveFilters(block.filter);
    }

    getFilterSummary(block) {
        return getFilterSummary(block.filter);
    }

    getFilteredBlock() {
        return this.state.dashboard?.blocks.find((block) => block.uid === this.state.filterUid);
    }

    openFilter(block) {
        block.filter ||= emptyFilter();
        this.state.filterUid = block.uid;
    }

    closeFilter() {
        this.state.filterUid = null;
    }

    onFilterChange(block, changes) {
        const previousDomain = JSON.stringify(buildFilterDomain(block.filter));
        const filter = { ...block.filter, ...changes };
        block.filter = filter;
        this.storeFilters();
        if (JSON.stringify(buildFilterDomain(filter)) === previousDomain) {
            return; // e.g. another date field chosen while no period is set
        }
        browser.clearTimeout(this.previewTimers.get(block.uid));
        this.previewTimers.set(
            block.uid,
            browser.setTimeout(() => this.refreshFilteredBlock(block), PREVIEW_DELAY)
        );
    }

    async refreshFilteredBlock(block) {
        this.previewTimers.delete(block.uid);
        const requestId = (block.previewRequestId || 0) + 1;
        block.previewRequestId = requestId;
        const data = await this.orm.call(BLOCK_MODEL, "get_block_data_filtered", [
            [block.id],
            buildFilterDomain(block.filter),
        ]);
        if (block.previewRequestId === requestId) {
            this.applyBlockData(block, data);
        }
    }

    // AI analysis --------------------------------------------------------------

    /**
     * Open the AI analysis of a block, on the data it currently shows. An analysis
     * is kept until the data of the block changes, so reopening it is free.
     */
    analyzeBlock(block) {
        const filterDomain = buildFilterDomain(block.filter);
        const key = `${block.version}|${JSON.stringify(filterDomain)}`;
        this.dialogService.add(BlockAiAnalysisDialog, {
            block,
            filterDomain,
            filterSummary: getFilterSummary(block.filter),
            analysis: block.aiAnalysis?.key === key ? block.aiAnalysis.text : "",
            onAnalyzed: (text) => {
                block.aiAnalysis = { key, text };
            },
        });
    }

    // Viewer -------------------------------------------------------------------

    startPresentation() {
        this.state.isPresenting = true;
    }

    stopPresentation() {
        this.state.isPresenting = false;
    }

    getCompanyName() {
        return user.activeCompany?.name || "";
    }

    /**
     * Export the dashboard as PDF with the browser: the dashboard is laid out for
     * A4 landscape pages (see dashboard_print.scss) and the print dialog opens, where
     * "Save as PDF" downloads it. Charts are printed exactly as they are displayed.
     */
    async exportPdf() {
        const { dashboard } = this.state;
        this.state.printDate = formatDateTime(luxon.DateTime.local());
        const pageStyle = document.createElement("style");
        pageStyle.textContent = "@page { size: A4 landscape; margin: 10mm; }";
        const documentTitle = document.title;
        document.head.append(pageStyle);
        document.body.classList.add("o_dynamic_dashboard_printing");
        // the browser proposes the document title as name of the PDF file
        document.title = dashboard.name;
        try {
            // let the print header render before the print layout is computed
            await new Promise((resolve) => browser.requestAnimationFrame(resolve));
            window.print();
        } finally {
            document.title = documentTitle;
            document.body.classList.remove("o_dynamic_dashboard_printing");
            pageStyle.remove();
        }
    }

    drillDown(block, group) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: group.label === block.name ? block.name : `${block.name} - ${group.label}`,
            res_model: block.model,
            domain: group.domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }

    openRecord(model, resId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
        });
    }

    // Drag and drop from the block palette ------------------------------------

    isPaletteDrag(ev) {
        return this.state.editMode && ev.dataTransfer.types.includes(BLOCK_DRAG_TYPE);
    }

    onCanvasDragOver(ev) {
        if (!this.isPaletteDrag(ev)) {
            return;
        }
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "copy";
        if (ev.target.closest(".o_dynamic_dashboard_drop_placeholder")) {
            return;
        }
        const cell = ev.target.closest(".o_dynamic_dashboard_cell");
        let dropIndex = this.state.dashboard.blocks.length;
        if (cell) {
            const rect = cell.getBoundingClientRect();
            const isAfter = ev.clientX > rect.left + rect.width / 2;
            dropIndex = parseInt(cell.dataset.index, 10) + (isAfter ? 1 : 0);
        }
        if (dropIndex !== this.state.dropIndex) {
            this.state.dropIndex = dropIndex;
        }
    }

    onCanvasDragLeave(ev) {
        if (!ev.currentTarget.contains(ev.relatedTarget)) {
            this.state.dropIndex = null;
        }
    }

    onCanvasDrop(ev) {
        if (!this.isPaletteDrag(ev)) {
            return;
        }
        ev.preventDefault();
        const blockType = ev.dataTransfer.getData(BLOCK_DRAG_TYPE);
        const index = this.state.dropIndex;
        this.state.dropIndex = null;
        this.addBlock(blockType, index);
    }

    onCanvasClick() {
        if (this.state.editMode) {
            this.selectBlock(null);
        }
    }

    onPaletteDragEnd() {
        this.state.dropIndex = null;
    }
}

registry.category("actions").add("odoo_dynamic_dashboard.dashboard", DynamicDashboardAction);
