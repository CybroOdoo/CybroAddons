import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { mockDate } from "@odoo/hoot-mock";
import { parseAnalysis } from "@odoo_dynamic_dashboard/ai_analysis/ai_analysis_dialog";
import {
    BLOCK_TYPES,
    autoArrangeBlocks,
    createBlock,
    getBlockConfig,
    getBlockIssue,
} from "@odoo_dynamic_dashboard/block_catalog/block_catalog";
import {
    buildFilterDomain,
    countActiveFilters,
    emptyFilter,
    getFilterSummary,
    getPeriodRange,
} from "@odoo_dynamic_dashboard/block_filter/block_filter";
import { getParentMenuOptions } from "@odoo_dynamic_dashboard/menu_dialog/menu_dialog";
import { buildSlides } from "@odoo_dynamic_dashboard/presentation/presentation";
import { patchTranslations } from "@web/../tests/web_test_helpers";

describe.current.tags("headless");

beforeEach(() => patchTranslations());

const block = (blockType, values = {}) => Object.assign(createBlock(blockType), { model: "res.partner" }, values);

describe("block catalog", () => {
    test("every block type is complete", () => {
        expect(BLOCK_TYPES.length).toBe(17);
        for (const info of BLOCK_TYPES) {
            expect(Boolean(info.label && info.help && info.icon && info.width && info.category)).toBe(true);
        }
    });

    test("new blocks", () => {
        const tile = createBlock("tile");
        expect(tile.id).toBe(false);
        expect(tile.width).toBe(3);
        expect(tile.customName).toBe(false);
        expect(createBlock("text").customName).toBe(true);
        expect(createBlock("tile").uid).not.toBe(tile.uid);
    });

    test("the suggested name is left to the server", () => {
        const tile = block("tile");
        expect("name" in getBlockConfig(tile)).toBe(false);
        tile.customName = true;
        expect(getBlockConfig(tile).name).toBe(tile.name);
        expect("uid" in getBlockConfig(tile)).toBe(false);
    });

    test("messages are translated", () => {
        patchTranslations({
            odoo_dynamic_dashboard: { "Choose the data to show": "Choisissez les données à afficher" },
        });
        expect(String(getBlockIssue(createBlock("tile")))).toBe("Choisissez les données à afficher");
    });

    test("configuration issues", () => {
        expect(String(getBlockIssue(createBlock("tile")))).toBe("Choose the data to show");
        expect(getBlockIssue(block("tile"))).toBe(false);
        expect(String(getBlockIssue(block("tile", { aggregate: "sum" })))).toBe("Choose the field to measure");
        expect(String(getBlockIssue(block("bar")))).toBe("Choose how to group the data");
        expect(String(getBlockIssue(block("pivot", { group_by: "type" })))).toBe("Choose the second field to group by");
        expect(getBlockIssue(block("pivot", { group_by: "type", sub_group_by: "country_id" }))).toBe(false);
        expect(getBlockIssue(block("record_list"))).toBe(false);
        expect(getBlockIssue(createBlock("text"))).toBe(false);
    });
});

describe("auto arrange", () => {
    test("key figures first, in full rows, then charts and tables", () => {
        const blocks = [
            block("table"), block("tile"), block("bar"), block("pie"), block("tile"), block("view"),
            block("line"), block("tile"),
        ];
        const arranged = autoArrangeBlocks(blocks);
        expect(arranged.map((b) => b.block_type)).toEqual([
            "tile", "tile", "tile", "bar", "line", "pie", "table", "view",
        ]);
        // 3 tiles share a row, 2 wide charts a row, a lone chart or table takes the full width
        expect(arranged.map((b) => b.width)).toEqual([4, 4, 4, 6, 6, 12, 12, 12]);
    });

    test("text blocks start sections", () => {
        const arranged = autoArrangeBlocks([
            block("bar"), block("tile"), createBlock("text"), block("table"), block("tile"),
        ]);
        expect(arranged.map((b) => b.block_type)).toEqual(["tile", "bar", "text", "tile", "table"]);
        expect(arranged.map((b) => b.width)).toEqual([12, 12, 12, 12, 12]);
    });

    test("rows of at most 4 key figures", () => {
        const arranged = autoArrangeBlocks([1, 2, 3, 4, 5, 6].map(() => block("tile")));
        expect(arranged.map((b) => b.width)).toEqual([3, 3, 3, 3, 6, 6]);
    });
});

describe("slides", () => {
    test("title, key figures together, one slide per chart, sections", () => {
        const slides = buildSlides([
            block("tile"), block("gauge"), createBlock("text"), block("bar"), block("progress"), block("table"),
        ]);
        expect(slides.map((slide) => slide.type)).toEqual(["title", "kpis", "section", "block", "kpis", "block"]);
        expect(slides[1].blocks.length).toBe(2);
    });

    test("at most 8 key figures per slide", () => {
        const slides = buildSlides(Array.from({ length: 10 }, () => block("tile")));
        expect(slides.map((slide) => slide.blocks?.length || 0)).toEqual([0, 8, 2]);
    });
});

describe("block filters", () => {
    test("no filter", () => {
        expect(countActiveFilters(undefined)).toBe(0);
        expect(countActiveFilters(emptyFilter())).toBe(0);
        expect(buildFilterDomain(emptyFilter())).toEqual([]);
        expect(getFilterSummary(emptyFilter())).toBe("");
    });

    test("periods", () => {
        mockDate("2026-10-15 10:30:00");
        const range = (period) => getPeriodRange(period).map((date) => date.toISODate());
        expect(range("today")).toEqual(["2026-10-15", "2026-10-16"]);
        expect(range("this_month")).toEqual(["2026-10-01", "2026-11-01"]);
        expect(range("this_quarter")).toEqual(["2026-10-01", "2027-01-01"]);
        expect(range("this_year")).toEqual(["2026-01-01", "2027-01-01"]);
        expect(range("last_7_days")).toEqual(["2026-10-09", "2026-10-16"]);
        expect(range("last_12_months")).toEqual(["2025-11-01", "2026-11-01"]);
        expect(getPeriodRange("custom", "2026-01-05", "").map((date) => date?.toISODate() ?? null)).toEqual([
            "2026-01-05", null,
        ]);
        expect(getPeriodRange("all")).toEqual([null, null]);
    });

    test("domain of a period on a date field", () => {
        mockDate("2026-10-15 10:30:00");
        const filter = { ...emptyFilter(), dateField: "date_order", dateFieldType: "date", period: "this_month" };
        expect(countActiveFilters(filter)).toBe(1);
        expect(buildFilterDomain(filter)).toEqual([
            "&", ["date_order", ">=", "2026-10-01"], ["date_order", "<", "2026-11-01"],
        ]);
        expect(String(getFilterSummary(filter))).toBe("This month");
        // a custom range without dates does not filter
        expect(countActiveFilters({ ...filter, period: "custom" })).toBe(0);
    });

    test("domain of values and conditions", () => {
        const filter = {
            ...emptyFilter(),
            values: [
                { label: "Invoice", domain: [["type", "=", "invoice"]] },
                { label: "Contact", domain: [["type", "=", "contact"]] },
            ],
            conditions: [
                { field: "is_company", type: "boolean", label: "Is a Company", values: [true] },
                { field: "user_id", type: "many2one", label: "Salesperson", values: [2, 3], valueLabels: ["Mitchell", "Marc"] },
                { field: "city", type: "char", label: "City", values: ["Brussels"] },
                { field: "state", type: "selection", label: "Status", values: [] }, // not set: ignored
            ],
        };
        expect(countActiveFilters(filter)).toBe(4);
        expect(buildFilterDomain(filter)).toEqual([
            "&", "|", ["type", "=", "invoice"], ["type", "=", "contact"],
            "&", ["is_company", "=", true],
            "&", ["user_id", "in", [2, 3]],
            ["city", "ilike", "Brussels"],
        ]);
        expect(getFilterSummary(filter)).toBe(
            "Invoice, Contact · Is a Company: Yes · Salesperson: Mitchell, Marc · City: Brussels"
        );
    });
});

describe("AI analysis", () => {
    test("points and recommendation", () => {
        const { points, recommendation } = parseAnalysis(
            "- **Belgium** leads with 6 contacts.  \n\n* India has 4 deliveries.\nRecommendation: Clean the data."
        );
        expect(points).toEqual(["Belgium leads with 6 contacts.", "India has 4 deliveries."]);
        expect(recommendation).toBe("Clean the data.");
    });

    test("translated recommendation and answers without one", () => {
        expect(parseAnalysis("- Un point.\nRecommandation : Agir.").recommendation).toBe("Agir.");
        expect(parseAnalysis("- One.\n- Two.")).toEqual({ points: ["One.", "Two."], recommendation: "" });
        expect(parseAnalysis("")).toEqual({ points: [], recommendation: "" });
    });
});

describe("menu dialog", () => {
    test("apps and their sections can hold a dashboard", () => {
        const menus = {
            1: { id: 1, name: "Sales", children: [2, 3], actionID: 10 },
            2: { id: 2, name: "Orders", children: [4], actionID: false },
            3: { id: 3, name: "Reporting", children: [5], actionID: false },
            4: { id: 4, name: "Quotations", children: [], actionID: 11 },
            5: { id: 5, name: "Sales Analysis", children: [], actionID: 12 },
            6: { id: 6, name: "Contacts", children: [], actionID: 13 },
        };
        const menuService = {
            getApps: () => [menus[1], menus[6]],
            getMenu: (id) => menus[id],
        };
        expect(getParentMenuOptions(menuService)).toEqual([
            { id: 1, label: "Sales" },
            { id: 2, label: "Sales / Orders" },
            { id: 3, label: "Sales / Reporting" },
            { id: 6, label: "Contacts" },
        ]);
    });
});
