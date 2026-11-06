import { animationFrame, click, expect, fill, queryAllTexts, test } from "@odoo/hoot";
import { mailModels } from "@mail/../tests/mail_test_helpers";
import {
    defineModels,
    fields,
    models,
    mountView,
    onRpc,
} from "@web/../tests/web_test_helpers";

class Foo extends models.Model {
    name = fields.Char();
    amount = fields.Integer();
    date = fields.Date();
    state = fields.Selection({
        selection: [
            ["draft", "Draft"],
            ["done", "Done"],
            ["cancel", "Cancelled"],
        ],
    });

    _records = [
        { id: 1, name: "yop", amount: 10, date: "2017-01-25", state: "draft" },
        { id: 2, name: "blip", amount: 9, date: "2017-02-10", state: "done" },
        { id: 3, name: "gnap", amount: 17, date: "2017-03-05", state: "cancel" },
        { id: 4, name: "blip", amount: 4, date: "2017-04-01", state: "draft" },
    ];
}

defineModels({ ...mailModels, Foo });

const SEARCH_ROW = ".o_list_search_row";
// The first <th> of the search row is the record selector on desktop, so the
// text boxes are addressed by their container instead of the <th> position.
const NAME_BOX = `${SEARCH_ROW} .search-input-container:eq(0)`;
const AMOUNT_BOX = `${SEARCH_ROW} .search-input-container:eq(1)`;
const NAME_INPUT = `${NAME_BOX} input`;
const NAME_SEARCH_ICON = `${NAME_BOX} [data-icon='search']`;
const AMOUNT_INPUT = `${AMOUNT_BOX} input`;
const AMOUNT_SEARCH_ICON = `${AMOUNT_BOX} [data-icon='search']`;

const ARCH = `
    <list>
        <field name="name"/>
        <field name="amount"/>
        <field name="date"/>
        <field name="state"/>
    </list>
`;

// Hoot's click() does not wait for OWL to render nor for the search model
// to reload, so wait two frames after every interaction.
async function settle() {
    await animationFrame();
    await animationFrame();
}

async function mountSearchableList() {
    await mountView({ resModel: "foo", type: "list", arch: ARCH });
}

async function addTag(inputSelector, iconSelector, value) {
    await click(inputSelector);
    await fill(value);
    await click(iconSelector);
    await settle();
}

async function addNameTag(value) {
    await addTag(NAME_INPUT, NAME_SEARCH_ICON, value);
}

test("search row is rendered with one control per column type", async () => {
    await mountSearchableList();

    expect(SEARCH_ROW).toHaveCount(1);
    expect(`${SEARCH_ROW} .search-input-container input`).toHaveCount(2);
    expect(`${SEARCH_ROW} .date-input`).toHaveCount(2);
    expect(`${SEARCH_ROW} .custom-dropdown-toggle`).toHaveCount(1);
    expect(".o_data_row").toHaveCount(4);
});

test("adding a text tag filters the records and shows the tag", async () => {
    await mountSearchableList();

    await addNameTag("blip");

    expect(queryAllTexts(".search-tag")).toEqual(["blip"]);
    expect(".o_data_row").toHaveCount(2);
});

test("several tags in one column are combined with OR", async () => {
    await mountSearchableList();

    await addNameTag("yop");
    await addNameTag("gnap");

    expect(queryAllTexts(".search-tag")).toEqual(["yop", "gnap"]);
    expect(".o_data_row").toHaveCount(2);
});

test("a duplicated tag is not added twice", async () => {
    await mountSearchableList();

    await addNameTag("blip");
    await addNameTag("blip");

    expect(".search-tag").toHaveCount(1);
});

test("removing a tag restores the records", async () => {
    await mountSearchableList();

    await addNameTag("blip");
    expect(".o_data_row").toHaveCount(2);

    await click(".search-tag .tag-remove");
    await settle();

    expect(".search-tag").toHaveCount(0);
    expect(".o_data_row").toHaveCount(4);
});

test("number columns search with the exact match operator", async () => {
    const domains = [];
    onRpc("web_search_read", ({ kwargs }) => {
        domains.push(JSON.stringify(kwargs.domain));
    });
    await mountSearchableList();

    await addTag(AMOUNT_INPUT, AMOUNT_SEARCH_ICON, "10");

    expect(domains.at(-1)).toBe(JSON.stringify([["amount", "=", "10"]]));
});

test("text columns search with the ilike operator", async () => {
    const domains = [];
    onRpc("web_search_read", ({ kwargs }) => {
        domains.push(JSON.stringify(kwargs.domain));
    });
    await mountSearchableList();

    await addNameTag("bl");

    expect(domains.at(-1)).toBe(JSON.stringify([["name", "ilike", "bl"]]));
});

test("filters on different columns are combined with AND", async () => {
    const domains = [];
    onRpc("web_search_read", ({ kwargs }) => {
        domains.push(JSON.stringify(kwargs.domain));
    });
    await mountSearchableList();

    await addNameTag("blip");
    await addTag(AMOUNT_INPUT, AMOUNT_SEARCH_ICON, "9");

    // The domain is asserted instead of the rows: the search value is a
    // string ("9") and the mock server compares it strictly with the
    // integer 9, unlike the real ORM which converts it.
    expect(domains.at(-1)).toBe(
        JSON.stringify(["&", ["name", "ilike", "blip"], ["amount", "=", "9"]])
    );
});

test("selection column filters with one or several options", async () => {
    await mountSearchableList();

    await click(`${SEARCH_ROW} .custom-dropdown-toggle`);
    await settle();
    await click(".dropdown-item:contains('Draft')");
    await settle();
    expect(".o_data_row").toHaveCount(2);

    await click(".dropdown-item:contains('Done')");
    await settle();
    expect(".o_data_row").toHaveCount(3);
    expect(".dropdown-item .text-success").toHaveCount(2);

    await click(".dropdown-item:contains('Draft')");
    await settle();
    expect(".o_data_row").toHaveCount(1);
});
