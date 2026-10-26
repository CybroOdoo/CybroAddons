/**
 * Browser tours for the wm_base JS that the dashboard tours do not reach:
 * the sidebar navbar patch, the Sign Now client action, the graph renderer
 * patch, the email chatter shadow patch and the extra dashboard drill-downs.
 * Run by wm_base/tests/test_ui_js.py.
 */
import { registry } from "@web/core/registry";

const tours = registry.category("web_tour.tours");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const waitUntil = async (predicate, message, ms = 8000) => {
    const start = Date.now();
    while (Date.now() - start < ms) {
        if (await predicate()) {
            return;
        }
        await sleep(50);
    }
    throw new Error(`Timeout waiting for: ${message}`);
};
const body = () => document.body.classList;

// ---------------------------------------------------------------- navbar
tours.add("wm_navbar_tour", {
    steps: () => [
        {
            content: "The desktop sidebar is rendered",
            trigger: ".ef-desktop-sidebar .ef-sidebar-inner-toggle",
        },
        {
            content: "Collapse the sidebar",
            trigger: ".ef-desktop-sidebar .ef-sidebar-inner-toggle",
            run: "click",
        },
        {
            content: "The collapsed state is applied and persisted",
            trigger: ".ef-desktop-sidebar.collapsed",
            run() {
                if (!body().contains("ef-sidebar-collapsed")) {
                    throw new Error("body is missing ef-sidebar-collapsed");
                }
                if (localStorage.getItem("ef_sidebar_collapsed") !== "true") {
                    throw new Error("collapsed state was not stored");
                }
            },
        },
        {
            content: "Expand the sidebar again",
            trigger: ".ef-desktop-sidebar .ef-sidebar-inner-toggle",
            run: "click",
        },
        {
            content: "The expanded state is applied and persisted",
            trigger: ".ef-desktop-sidebar:not(.collapsed)",
            run() {
                if (body().contains("ef-sidebar-collapsed")) {
                    throw new Error("body still has ef-sidebar-collapsed");
                }
                if (localStorage.getItem("ef_sidebar_collapsed") !== "false") {
                    throw new Error("expanded state was not stored");
                }
            },
        },
        {
            content: "Open the apps dashboard from the brand",
            trigger: ".ef-custom-brand",
            run: "click",
        },
        {
            content: "The apps dashboard is active",
            trigger: "body.ef-apps-dashboard-active",
        },
        {
            content: "Close the apps dashboard from the brand",
            trigger: ".ef-custom-brand",
            run: "click",
        },
        {
            content: "The apps dashboard is closed",
            trigger: "body:not(.ef-apps-dashboard-active)",
        },
    ],
});

tours.add("wm_navbar_mobile_tour", {
    steps: () => [
        {
            content: "The mobile sidebar toggle is shown",
            trigger: ".ef-sidebar-toggle-btn",
            run: "click",
        },
        {
            content: "The mobile drawer is opened",
            trigger: ".ef-mobile-sidebar.mobile-open",
            run() {
                if (!body().contains("ef-mobile-sidebar-open")) {
                    throw new Error("body is missing ef-mobile-sidebar-open");
                }
            },
        },
        {
            content: "Close the drawer",
            trigger: ".ef-mobile-sidebar .btn-close",
            run: "click",
        },
        {
            content: "The drawer is closed",
            trigger: ".ef-mobile-sidebar:not(.mobile-open)",
            run() {
                if (body().contains("ef-mobile-sidebar-open")) {
                    throw new Error("body still has ef-mobile-sidebar-open");
                }
            },
        },
    ],
});

// -------------------------------------------------------------- sign now
const dropFile = (target, file) => {
    const transfer = new DataTransfer();
    transfer.items.add(file);
    target.dispatchEvent(new DragEvent("drop", { dataTransfer: transfer, bubbles: true, cancelable: true }));
};

tours.add("wm_sign_now_tour", {
    steps: () => [
        {
            content: "The upload drop zone is shown",
            trigger: ".o_wm_sign_now_container .o_upload_dropzone",
        },
        {
            content: "Dragging over highlights the drop zone",
            trigger: ".o_upload_dropzone",
            run() {
                this.anchor.dispatchEvent(new DragEvent("dragenter", { bubbles: true, cancelable: true }));
            },
        },
        {
            content: "The drop zone is highlighted",
            trigger: ".o_upload_dropzone.border-primary",
        },
        {
            content: "Leaving removes the highlight",
            trigger: ".o_upload_dropzone",
            run() {
                this.anchor.dispatchEvent(new DragEvent("dragleave", { bubbles: true, cancelable: true }));
            },
        },
        {
            content: "The highlight is gone",
            trigger: ".o_upload_dropzone:not(.border-primary)",
        },
        {
            content: "Drop a non-PDF file",
            trigger: ".o_upload_dropzone",
            run() {
                dropFile(this.anchor, new File(["hello"], "notes.txt", { type: "text/plain" }));
            },
        },
        {
            content: "Only PDF documents are accepted",
            trigger: ".o_notification:contains(Only PDF documents are allowed)",
        },
        {
            content: "Pick a non-PDF file through the input",
            trigger: ".o_wm_sign_now_container input[type=file]:hidden",
            run() {
                const transfer = new DataTransfer();
                transfer.items.add(new File(["hello"], "notes.txt", { type: "text/plain" }));
                this.anchor.files = transfer.files;
                this.anchor.dispatchEvent(new Event("change", { bubbles: true }));
            },
        },
        {
            content: "The input rejects it as well",
            trigger: ".o_notification:contains(Only PDF documents are allowed) ~ .o_notification:contains(Only PDF documents are allowed), .o_notification:contains(Only PDF documents are allowed) + .o_notification",
            run() {
                const count = document.querySelectorAll(".o_notification").length;
                if (count < 2) {
                    throw new Error(`expected two notifications, got ${count}`);
                }
            },
        },
        {
            content: "Generate the sample contract",
            trigger: ".o_upload_dropzone button:contains(Try a sample contract)",
            run: "click",
        },
        {
            content: "The designer iframe is opened",
            trigger: "#sign_designer_iframe",
            run() {
                if (!this.anchor.getAttribute("src").includes("/wm_signature/template/edit/")) {
                    throw new Error("unexpected editor url");
                }
            },
        },
        {
            content: "Exit the designer",
            trigger: ".o_cp_right button:contains(Exit Designer)",
            run: "click",
        },
        {
            content: "Back on the upload screen",
            trigger: ".o_upload_dropzone",
        },
        {
            content: "Open the designer again",
            trigger: ".o_upload_dropzone button:contains(Try a sample contract)",
            run: "click",
        },
        {
            content: "The designer is open",
            trigger: "#sign_designer_iframe",
            run() {
                window.postMessage({ type: "discard" }, "*");
            },
        },
        {
            content: "Discard returns to the upload screen",
            trigger: ".o_upload_dropzone",
        },
        {
            content: "Open the designer a third time",
            trigger: ".o_upload_dropzone button:contains(Try a sample contract)",
            run: "click",
        },
        {
            content: "Signature completion is reported",
            trigger: "#sign_designer_iframe",
            run() {
                window.postMessage({ type: "signature_complete" }, "*");
            },
        },
        {
            content: "The success notification is shown",
            trigger: ".o_notification:contains(Document successfully signed)",
        },
        {
            content: "The upload screen is back",
            trigger: ".o_upload_dropzone",
            run() {
                window.postMessage({ type: "unrelated" }, "*");
            },
        },
        {
            content: "Unknown messages are ignored",
            trigger: ".o_upload_dropzone",
        },
        {
            content: "Open the designer a fourth time",
            trigger: ".o_upload_dropzone button:contains(Try a sample contract)",
            run: "click",
        },
        {
            content: "Sending completion is reported",
            trigger: "#sign_designer_iframe",
            run() {
                window.postMessage({ type: "send_complete" }, "*");
            },
        },
        {
            content: "The sent notification is shown",
            trigger: ".o_notification:contains(Signature request successfully sent)",
        },
    ],
});

// ----------------------------------------------------------- graph patch
tours.add("wm_graph_renderer_tour", {
    steps: () => [
        {
            content: "The bar chart is rendered",
            trigger: ".o_graph_renderer .o_graph_canvas_container canvas",
            async run() {
                const canvas = this.anchor;
                await waitUntil(() => window.Chart && window.Chart.getChart(canvas), "chart instance");
                const options = window.Chart.getChart(canvas).options;
                for (const axis of ["x", "y"]) {
                    const ticks = options.scales[axis].ticks;
                    if (ticks.color !== "#1F2937") {
                        throw new Error(`${axis} ticks color is ${ticks.color}`);
                    }
                    if (ticks.font.weight !== "600" || ticks.font.size !== 12) {
                        throw new Error(`${axis} ticks font is not the patched one`);
                    }
                }
                const labels = options.plugins.legend.labels;
                if (labels.color !== "#1F2937") {
                    throw new Error(`legend color is ${labels.color}`);
                }
                const generated = labels.generateLabels(window.Chart.getChart(canvas));
                if (!generated.length || generated.some((l) => l.fontColor !== "#1F2937" || l.color !== "#1F2937")) {
                    throw new Error("legend labels are not recoloured");
                }
            },
        },
    ],
});

// -------------------------------------------------------- chatter shadow
tours.add("wm_chatter_shadow_tour", {
    steps: () => [
        {
            content: "The email message is displayed",
            trigger: ".o-mail-Message-body > .overflow-x-auto:not(.o-mail-Message-richBody)",
            async run() {
                const host = this.anchor;
                const fixed = () => host.shadowRoot && [...host.shadowRoot.querySelectorAll("style")]
                    .some((style) => style.textContent.includes("#1F2937"));
                try {
                    await waitUntil(fixed, "shadow fix style", 4000);
                } catch (e) {
                    const styles = host.shadowRoot
                        ? [...host.shadowRoot.querySelectorAll("style")].map((st) => st.textContent.slice(0, 60))
                        : "no shadow root";
                    throw new Error(`${e.message}: ${JSON.stringify(styles)}`);
                }
            },
        },
    ],
});

// ----------------------------------------------------- dashboard drilldowns
const dashboardDrilldown = (name, selector, breadcrumb) => {
    tours.add(name, {
        steps: () => [
            {
                content: "The dashboard is rendered",
                trigger: ".wm_dashboard_root .wm_db_title:contains(Operations Dashboard)",
            },
            {
                content: "The charts are drawn",
                trigger: ".wm_dashboard_root canvas",
            },
            {
                content: "Click the drill-down",
                trigger: `.wm_dashboard_root ${selector}`,
                run: "click",
            },
            {
                content: "The drill-down opens",
                trigger: `.o_breadcrumb:contains(${breadcrumb})`,
            },
        ],
    });
};
dashboardDrilldown("wm_dashboard_inspection_tour", ".kpi_inspection .sub_item[title='View passed inspections']", "Batch Inspections");
dashboardDrilldown("wm_dashboard_inspection_all_tour", ".kpi_inspection", "Batch Inspections");
dashboardDrilldown("wm_dashboard_legend_inspection_tour", ".legend_line[title='View failed inspections']", "Batch Inspections");
dashboardDrilldown("wm_dashboard_fleet_tour", ".kpi_fleet .kpi_main_val_wrap", "Fleet Vehicles");
dashboardDrilldown("wm_dashboard_orders_all_tour", ".kpi_orders", "Collection Orders");
dashboardDrilldown("wm_dashboard_efficiency_tour", ".legend_line[title='View on-time collection orders']", "Collection Orders");
dashboardDrilldown("wm_dashboard_awaiting_signature_tour", ".btn_view_all_link", "Awaiting Signature");
