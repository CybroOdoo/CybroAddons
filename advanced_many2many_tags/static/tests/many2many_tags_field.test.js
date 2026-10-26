/** @odoo-module */
import { describe, expect, test } from "@odoo/hoot";
import { click } from "@odoo/hoot-dom";
import {
    assignDialogTestEnv,
    mockService,
    mountWithCleanup,
} from "@web/../tests/web_test_helpers";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

describe("advanced_many2many_tags ConfirmationDialog extension", () => {
    describe.current.tags("desktop");

    test("dialog shows Open Form View button when resModel and recordResId are passed", async () => {
        assignDialogTestEnv();
        await mountWithCleanup(ConfirmationDialog, {
            props: {
                body: "Tag action dialog",
                close: () => {},
                confirm: () => {},
                resModel: "project.tags",
                recordResId: 15,
                openFormViewLabel: "Open Form View",
            },
        });
        expect(".modal-footer button:contains('Open Form View')").toHaveCount(1);
    });

    test("unrelated ConfirmationDialog does NOT show Open Form View button", async () => {
        assignDialogTestEnv();
        await mountWithCleanup(ConfirmationDialog, {
            props: {
                body: "Are you sure you want to delete this record?",
                close: () => {},
                confirm: () => {},
                cancel: () => {},
            },
        });
        expect(".modal-footer button:contains('Open Form View')").toHaveCount(0);
    });

    test("clicking Open Form View button triggers action with dynamic resModel and recordResId", async () => {
        assignDialogTestEnv();
        let doActionPayload = null;
        let isClosed = false;
        mockService("action", {
            doAction: (action) => {
                doActionPayload = action;
            },
        });
        await mountWithCleanup(ConfirmationDialog, {
            props: {
                body: "Tag dialog",
                close: () => {
                    isClosed = true;
                },
                confirm: () => {},
                resModel: "crm.tag",
                recordResId: 99,
                openFormViewLabel: "Open Form View",
            },
        });
        await click(".modal-footer button:contains('Open Form View')");
        expect(doActionPayload).toEqual({
            type: "ir.actions.act_window",
            res_model: "crm.tag",
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            res_id: 99,
        });
        expect(isClosed).toBe(true);
    });
});
