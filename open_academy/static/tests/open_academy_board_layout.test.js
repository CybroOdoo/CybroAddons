import "@open_academy/js/open_academy_board_layout";

import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { beforeEach, describe, expect, test } from "@odoo/hoot";
import {
    contains,
    defineModels,
    fields,
    models,
    mountView,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { BoardAction } from "@board/board_action";

class Board extends models.Model {}

class Partner extends models.Model {
    name = fields.Char({ string: "Displayed name", searchable: true });
    foo = fields.Char({ string: "Foo", searchable: true });

    _records = [
        { id: 1, name: "first record", foo: "alpha" },
        { id: 2, name: "second record", foo: "beta" },
        { id: 3, name: "third record", foo: "gamma" },
    ];

    _views = {
        "list,4": '<list string="Partner"><field name="foo"/></list>',
    };
}

defineModels([Board, Partner]);
defineMailModels();

beforeEach(() => {
    BoardAction.cache = {};
});

describe.tags("desktop");
describe("openacademy_board_layout", () => {
    test("redistributes dashboard actions when the layout grows", async () => {
        onRpc("/web/action/load", () => ({
            res_model: "partner",
            views: [[4, "list"]],
        }));
        onRpc("/web/view/edit_custom", () => true);

        await mountView({
            type: "form",
            resModel: "board",
            arch: `
                <form string="Session Dashboard" js_class="board">
                    <board style="1">
                        <column>
                            <action string="Sessions" name="51" view_mode="list" context="{}" domain="[]"/>
                            <action string="Courses" name="52" view_mode="list" context="{}" domain="[]"/>
                            <action string="Attendees" name="53" view_mode="list" context="{}" domain="[]"/>
                        </column>
                    </board>
                </form>`,
        });

        expect('.o-dashboard-column[data-idx="0"] .o-dashboard-action').toHaveCount(3);

        await contains(".o-dashboard-header .dropdown img").click();
        await contains(".dropdown-item:nth-child(4)").click();

        expect("div.o-dashboard-layout-1-2").toHaveCount(1);
        expect('.o-dashboard-column[data-idx="0"] .o-dashboard-action').toHaveCount(1);
        expect('.o-dashboard-column[data-idx="1"] .o-dashboard-action').toHaveCount(2);
    });
});
