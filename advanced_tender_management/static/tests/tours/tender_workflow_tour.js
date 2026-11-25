import { formatDate } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";

const { DateTime } = luxon;
const tours = registry.category("web_tour.tours");

/** Date `days` from today, as typed in a date field of the user's language. */
function day(days) {
    return formatDate(DateTime.now().plus({ days }));
}

/** Pick `value` in the many2one field `name` (of the selected list row when `inRow`). */
function many2one(name, value, inRow = false, item = `:text(${value})`) {
    const scope = inRow ? ".o_selected_row " : ".o_form_renderer ";
    return [
        {
            content: `Type "${value}" in ${name}`,
            trigger: `${scope}.o_field_widget[name='${name}'] input`,
            run: `edit ${value}`,
        },
        {
            content: `Choose "${value}" for ${name}`,
            trigger: `.ui-menu-item > a${item}`,
            run: "click",
        },
    ];
}

/** Put a file named `name` with `content` in the file input `selector`. */
async function setFile(selector, name, content, type) {
    const input = document.querySelector(selector);
    if (!input) {
        throw new Error(`No file input ${selector}`);
    }
    const transfer = new DataTransfer();
    transfer.items.add(new File([content], name, { type }));
    input.files = transfer.files;
    input.dispatchEvent(new Event("change", { bubbles: true }));
}

/** Type a price in a number input and leave the field, as a vendor does. */
function enterPrice(value) {
    return function ({ anchor }) {
        anchor.focus();
        anchor.value = value;
        anchor.dispatchEvent(new Event("input", { bubbles: true }));
        anchor.dispatchEvent(new Event("change", { bubbles: true }));
        anchor.blur();
    };
}

function clickButton(name, content) {
    return { content, trigger: `button[name='${name}']:enabled`, run: "click" };
}

function checkStage(label) {
    return {
        content: `Stage is ${label}`,
        trigger: `.o_statusbar_status .o_arrow_button_current:contains(${label})`,
    };
}

// Create a tender in the backend with a decimal quantity and confirm it.
tours.add("tender_ui_create_confirm", {
    steps: () => [
        { content: "New tender", trigger: ".o_list_button_add", run: "click" },
        {
            content: "Tender name",
            trigger: ".o_field_widget[name='name'] :is(input, textarea)",
            run: "edit UI Tender",
        },
        ...many2one("responsible_id", "Tender Responsible"),
        ...many2one("tender_category_id", "UI Category"),
        {
            content: "Tender start date",
            trigger: ".o_field_widget[name='tender_start_date'] input",
            run: `edit ${day(0)}`,
        },
        {
            content: "Tender end date",
            trigger: ".o_field_widget[name='tender_end_date'] input",
            run: `edit ${day(10)}`,
        },
        {
            content: "Bid start date",
            trigger: ".o_field_widget[name='bid_start_date'] input",
            run: `edit ${day(0)}`,
        },
        {
            content: "Bid end date",
            trigger: ".o_field_widget[name='bid_end_date'] input",
            run: `edit ${day(5)}`,
        },
        {
            content: "Open the tender type list",
            trigger: ".o_field_widget[name='tender_type'] .o_select_menu input",
            run: "click",
        },
        {
            content: "Tender type",
            trigger: ".o_select_menu_menu .o_select_menu_item:contains(Single vendor)",
            run: "click",
        },
        {
            content: "Street",
            trigger: ".o_field_widget[name='address_street'] input",
            run: "edit 1 Tender Street",
        },
        {
            content: "City",
            trigger: ".o_field_widget[name='address_city'] input",
            run: "edit Kochi",
        },
        ...many2one("address_country_id", "India"),
        ...many2one("address_state_id", "Kerala", false, ":contains(Kerala):contains(IN)"),
        {
            content: "Add a product line",
            trigger: ".o_field_x2many_list_row_add button:contains(Add a product)",
            run: "click",
        },
        ...many2one("product_id", "UI Gloves", true),
        {
            content: "Line description",
            trigger: ".o_selected_row .o_field_widget[name='name'] :is(input, textarea)",
            run: "edit Nitrile gloves",
        },
        {
            content: "Decimal quantity",
            trigger: ".o_selected_row .o_field_widget[name='product_qty'] input",
            run: "edit 2.5",
        },
        {
            content: "Add a second product line",
            trigger: ".o_field_x2many_list_row_add button:contains(Add a product)",
            run: "click",
        },
        {
            content: "The new, second row is being edited",
            trigger: ".o_data_row:eq(1).o_selected_row",
        },
        ...many2one("product_id", "UI Masks", true),
        {
            content: "Second line description",
            trigger: ".o_selected_row .o_field_widget[name='name'] :is(input, textarea)",
            run: "edit Surgical masks",
        },
        {
            content: "Second quantity",
            trigger: ".o_selected_row .o_field_widget[name='product_qty'] input",
            run: "edit 2",
        },
        {
            content: "Open the Description tab",
            trigger: ".o_notebook .nav-link:contains(Description)",
            run: "click",
        },
        {
            content: "Description",
            trigger: ".o_field_widget[name='description'] .odoo-editor-editable",
            run: "editor Tender for gloves and masks",
        },
        { content: "Save", trigger: ".o_form_button_save", run: "click" },
        { content: "Saved", trigger: ".o_form_button_save:not(:visible)" },
        clickButton("action_confirm_tender", "Confirm the tender"),
        checkStage("Confirmed"),
        {
            content: "Open the Product tab",
            trigger: ".o_notebook .nav-link:contains(Product)",
            run: "click",
        },
        {
            content: "Quantity shows two decimals",
            trigger: ".o_data_row td[name='product_qty']:contains(2.50)",
        },
    ],
});

// A logged-in vendor submits prices and a document on the tender page.
tours.add("tender_ui_vendor_bid", {
    steps: () => [
        { content: "Tender page", trigger: ".tender_details_page" },
        {
            content: "Quantity shown with decimals",
            trigger: ".product_row .product_qty[data-qty='2.5']:contains(2.50)",
        },
        {
            content: "Price of the first product",
            trigger: ".product_row:eq(0) .vendor_bid",
            run: enterPrice("12.5"),
        },
        {
            content: "Price of the second product",
            trigger: ".product_row:eq(1) .vendor_bid",
            run: enterPrice("8"),
        },
        {
            content: "Line total uses the decimal quantity",
            trigger: ".product_row:eq(0) .total_price:contains(31.25)",
        },
        {
            content: "Grand total",
            trigger: ".grand_total:contains(47.25)",
        },
        {
            content: "Attach the bid document",
            trigger: "input#att:not(:visible)",
            run: () => setFile("input#att", "bid.pdf", "%PDF-1.4 bid", "application/pdf"),
        },
        {
            content: "Submit the bid",
            trigger: ".tender-bid-form button[type='submit']:contains(Register)",
            run: "click",
            expectUnloadPage: true,
        },
        { content: "Bid submitted", trigger: "body:contains(Thank You!)" },
    ],
});

// The vendor asks to edit the submitted bid.
tours.add("tender_ui_vendor_edit_request", {
    steps: () => [
        {
            content: "Submitted prices are read-only",
            trigger: ".tender_details_page:not(:has(.vendor_bid))",
        },
        {
            content: "Request edit",
            trigger: ".edit-request-btn",
            run: "click",
            expectUnloadPage: true,
        },
        { content: "Request sent", trigger: "body:contains(Thank You!)" },
    ],
});

// The vendor follows the bid in the portal.
tours.add("tender_ui_vendor_portal", {
    steps: () => [
        { content: "Bid listed in My Tenders", trigger: "table:contains(UI Tender)" },
    ],
});

// The tender responsible approves the edit request.
tours.add("tender_ui_approve_edit", {
    steps: () => [
        clickButton("action_approve_edit_request", "Approve the edit request"),
        { content: "Bid reopened", trigger: ".ribbon:contains(Pending)" },
    ],
});

// A bid received outside the website is entered and submitted in the backend.
tours.add("tender_ui_backend_bid", {
    steps: () => [
        ...many2one("vendor_id", "UI Vendor Two"),
        ...many2one("tender_id", "UI Tender"),
        {
            content: "Lines come from the tender, with its quantity",
            trigger: ".o_data_row:eq(0) td[name='product_qty']:contains(2.50)",
        },
        {
            content: "Lines cannot be added",
            trigger: ".o_field_widget[name='tender_bid_products_ids']:not(:has(.o_field_x2many_list_row_add))",
        },
        {
            content: "Open the first line",
            trigger: ".o_data_row:eq(0) td[name='product_price']",
            run: "click",
        },
        {
            content: "The first line is being edited",
            trigger: ".o_data_row:eq(0).o_selected_row",
        },
        {
            content: "Quantity is read-only",
            trigger: ".o_selected_row td[name='product_qty']:not(:has(input))",
        },
        {
            content: "Price of the first line",
            trigger: ".o_selected_row .o_field_widget[name='product_price'] input",
            run: "edit 11",
        },
        {
            content: "Open the second line",
            trigger: ".o_data_row:eq(1) td[name='product_price']",
            run: "click",
        },
        {
            content: "The second line is being edited",
            trigger: ".o_data_row:eq(1).o_selected_row",
        },
        {
            content: "Price of the second line",
            trigger: ".o_selected_row .o_field_widget[name='product_price'] input",
            run: "edit 9",
        },
        { content: "Save", trigger: ".o_form_button_save", run: "click" },
        { content: "Saved", trigger: ".o_form_button_save:not(:visible)" },
        {
            content: "Total of the bid",
            trigger: ".o_field_widget[name='total_bidding_amount']:contains(45.50)",
        },
        clickButton("action_submit_bid", "Submit the bid"),
        {
            content: "Confirm the submission",
            trigger: ".modal-footer button.btn-primary",
            run: "click",
        },
        { content: "Bid submitted", trigger: ".ribbon:contains(Confirmed)" },
        checkStage("Bid Close"),
    ],
});

// Bids are qualified, the cheapest one is selected and bought.
tours.add("tender_ui_evaluate_select", {
    steps: () => [
        checkStage("Bid Evaluation"),
        clickButton("action_get_bids", "Open all bids"),
        {
            content: "Bid of vendor one",
            trigger: ".o_data_row:contains(UI Vendor One) td[name='name']",
            run: "click",
        },
        { content: "Bid form of vendor one", trigger: ".o_form_view .o_field_widget[name='vendor_id']:contains(UI Vendor One)" },
        clickButton("action_qualify", "Qualify vendor one"),
        {
            content: "Vendor one qualified",
            trigger: ".o_field_widget[name='qualification_stage']:contains(Qualified)",
        },
        { content: "Back to the bids", trigger: ".breadcrumb-item a:contains(All Bids)", run: "click" },
        {
            content: "Bid of vendor two",
            trigger: ".o_data_row:contains(UI Vendor Two) td[name='name']",
            run: "click",
        },
        { content: "Bid form of vendor two", trigger: ".o_form_view .o_field_widget[name='vendor_id']:contains(UI Vendor Two)" },
        clickButton("action_qualify", "Qualify vendor two"),
        {
            content: "Vendor two qualified",
            trigger: ".o_field_widget[name='qualification_stage']:contains(Qualified)",
        },
        { content: "Back to all bids", trigger: ".breadcrumb-item a:contains(All Bids)", run: "click" },
        { content: "Bids list", trigger: ".o_list_view .o_data_row:contains(UI Vendor Two)" },
        { content: "Back to the tender", trigger: ".breadcrumb-item a:contains(UI Tender)", run: "click" },
        {
            content: "Two qualified bids",
            trigger: "button[name='action_get_qualified_bids'] .o_stat_value:contains(2)",
        },
        clickButton("action_start_selection", "Start selection"),
        checkStage("Bid Selection"),
        clickButton("action_select_final_bid", "Select the bid"),
        {
            content: "Cheapest bid proposed",
            trigger: ".modal .o_field_widget[name='tender_bid_id'] input",
            run({ anchor }) {
                if (!anchor.value) {
                    throw new Error("No bid proposed in the Bid Selection wizard");
                }
            },
        },
        {
            content: "Confirm the purchase",
            trigger: ".modal button[name='action_confirm_purchase']",
            run: "click",
        },
        checkStage("Closed"),
        clickButton("action_get_purchase_order", "Open the purchase order"),
        { content: "Order of vendor two", trigger: ".o_data_row:contains(UI Vendor Two)" },
    ],
});

// Product-wise tender: one line chosen per product, then the bids confirmed.
tours.add("tender_ui_product_wise", {
    steps: () => [
        clickButton("action_get_evaluation_bids", "Open the bids by product"),
        { content: "Gloves group", trigger: ".o_group_header:contains(UI Gloves)", run: "click" },
        {
            content: "Choose vendor one for gloves",
            trigger: ".o_data_row:contains(UI Vendor One):contains(UI Gloves) button[name='action_confirm_bid']",
            run: "click",
        },
        {
            content: "Gloves line of vendor one selected",
            trigger: ".o_data_row:contains(UI Vendor One):contains(UI Gloves) button[name='action_selected_bid']",
        },
        { content: "Masks group", trigger: ".o_group_header:contains(UI Masks)", run: "click" },
        {
            content: "Choose vendor two for masks",
            trigger: ".o_data_row:contains(UI Vendor Two):contains(UI Masks) button[name='action_confirm_bid']",
            run: "click",
        },
        {
            content: "Masks line of vendor two selected",
            trigger: ".o_data_row:contains(UI Vendor Two):contains(UI Masks) button[name='action_selected_bid']",
        },
        { content: "Back to the tender", trigger: ".breadcrumb-item a:contains(UI Product Tender)", run: "click" },
        clickButton("action_start_selection", "Start selection"),
        clickButton("action_confirm_bids", "Confirm the bids"),
        checkStage("Closed"),
        {
            content: "Two purchase orders",
            trigger: "button[name='action_get_purchase_order'] .o_stat_value:contains(2)",
        },
    ],
});

// Import product lines from an XLSX file prepared by the test.
tours.add("tender_ui_import_lines", {
    steps: () => [
        clickButton("action_import_tender_product_wizard", "Open the import"),
        {
            content: "Attach the XLSX file",
            trigger: ".modal .o_field_widget[name='file'] input[type='file']:not(:visible)",
            async run() {
                const response = await fetch("/web/dataset/call_kw/ir.attachment/search_read", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {
                            model: "ir.attachment",
                            method: "search_read",
                            args: [[["name", "=", "ui_tender_import.xlsx"]], ["id"]],
                            kwargs: {},
                        },
                    }),
                });
                const { result } = await response.json();
                const file = await fetch(`/web/content/${result[0].id}`);
                const bytes = new Uint8Array(await file.arrayBuffer());
                await setFile(
                    ".modal .o_field_widget[name='file'] input[type='file']",
                    "lines.xlsx",
                    bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                );
            },
        },
        {
            content: "File loaded",
            trigger: ".modal .o_field_widget[name='file'] input:value(lines.xlsx)",
        },
        {
            content: "Import",
            trigger: ".modal button[name='action_import_tender_product_lines']",
            run: "click",
        },
        {
            content: "Imported line with its decimal quantity",
            trigger: ".o_data_row:contains(Imported gloves) td[name='product_qty']:contains(1.50)",
        },
        { content: "Imported section", trigger: ".o_is_line_section:contains(Imported section)" },
    ],
});

// Import refuses a quantity that is not a number.
tours.add("tender_ui_import_bad_quantity", {
    steps: () => [
        clickButton("action_import_tender_product_wizard", "Open the import"),
        {
            content: "Attach the XLSX file",
            trigger: ".modal .o_field_widget[name='file'] input[type='file']:not(:visible)",
            async run() {
                const response = await fetch("/web/dataset/call_kw/ir.attachment/search_read", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {
                            model: "ir.attachment",
                            method: "search_read",
                            args: [[["name", "=", "ui_tender_bad_import.xlsx"]], ["id"]],
                            kwargs: {},
                        },
                    }),
                });
                const { result } = await response.json();
                const file = await fetch(`/web/content/${result[0].id}`);
                const bytes = new Uint8Array(await file.arrayBuffer());
                await setFile(
                    ".modal .o_field_widget[name='file'] input[type='file']",
                    "bad.xlsx",
                    bytes,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                );
            },
        },
        {
            content: "File loaded",
            trigger: ".modal .o_field_widget[name='file'] input:value(bad.xlsx)",
        },
        {
            content: "Import",
            trigger: ".modal button[name='action_import_tender_product_lines']",
            run: "click",
        },
        {
            content: "Clear error naming the row",
            trigger: ".o_error_dialog:contains(Row 2), .modal:contains(Row 2)",
        },
    ],
});

// A visitor registers as a vendor from the website.
tours.add("tender_ui_vendor_register", {
    steps: () => [
        {
            content: "Company name",
            trigger: ".vendor-registration-form input[name='name']",
            run: "edit UI Registered Vendor",
        },
        { content: "Street", trigger: "input[name='street']", run: "edit 5 Vendor Road" },
        { content: "City", trigger: "input[name='city']", run: "edit Kochi" },
        { content: "ZIP", trigger: "input[name='zip']", run: "edit 682001" },
        { content: "Country", trigger: "select[name='country']", run: "selectByLabel India" },
        { content: "Phone", trigger: "input[name='phone']", run: "edit 9999999999" },
        {
            content: "Email",
            trigger: "input[name='email']",
            run: "edit ui.registered.vendor@example.com",
        },
        { content: "Category", trigger: "select[name='category']", run: "selectByLabel UI Category" },
        {
            content: "Register",
            trigger: ".vendor-registration-form button[type='submit']",
            run: "click",
            expectUnloadPage: true,
        },
        { content: "Registered", trigger: "body:contains(Thank You!)" },
    ],
});

// Tenders open for bidding appear in the website tenders block.
tours.add("tender_ui_website_list", {
    steps: () => [
        { content: "Tender card", trigger: ".oe_tender_card:contains(UI Tender)" },
        {
            content: "Open the tender",
            trigger: ".oe_tender_card:contains(UI Tender) a.oe_tender_button",
            run: "click",
            expectUnloadPage: true,
        },
        { content: "Tender page", trigger: ".tender_details_page:contains(UI Tender)" },
    ],
});

// The dashboard loads its figures.
tours.add("tender_ui_dashboard", {
    steps: () => [{ content: "Tender count tile", trigger: "#tenders .tile-count" }],
});

/** Steps checking the Tenders card of the portal home page once counters loaded. */
function portalHome() {
    return [
        {
            content: "Portal home loaded its counters",
            trigger: ".o_portal_my_home:not(:has(.o_portal_doc_spinner))",
        },
    ];
}

// A vendor with bids sees the Tenders card with the number of bids.
tours.add("tender_ui_portal_card_count", {
    steps: () => [
        ...portalHome(),
        {
            content: "Tenders card shows the two bids",
            trigger: ".o_portal_index_card:not(.d-none):contains(Tenders) [data-placeholder_count='tender_bid_count']:not(.d-none):text(2)",
        },
        {
            content: "Open the card",
            trigger: ".o_portal_index_card:contains(Tenders) a",
            run: "click",
            expectUnloadPage: true,
        },
        { content: "Bids of the vendor", trigger: "table:contains(Bid Reference)" },
    ],
});

// A vendor without bids sees the card, without a count.
tours.add("tender_ui_portal_card_no_count", {
    steps: () => [
        ...portalHome(),
        {
            content: "Tenders card visible",
            trigger: ".o_portal_index_card:not(.d-none):contains(Tenders):visible",
        },
        {
            content: "No bid count on the card",
            trigger: ".o_portal_index_card:contains(Tenders) [data-placeholder_count='tender_bid_count'].d-none:not(:visible)",
        },
    ],
});

// A customer who is not a vendor and has no bid does not see the card.
tours.add("tender_ui_portal_card_hidden", {
    steps: () => [
        ...portalHome(),
        {
            content: "Tenders card hidden",
            trigger: ".o_portal_index_card.d-none:contains(Tenders):not(:visible)",
        },
    ],
});
