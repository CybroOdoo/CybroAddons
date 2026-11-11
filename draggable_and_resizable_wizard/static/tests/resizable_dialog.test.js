import { animationFrame, expect, queryOne, resize, test } from "@odoo/hoot";
import { Component, xml } from "@odoo/owl";
import { assignDialogTestEnv, contains, mountWithCleanup } from "@web/../tests/web_test_helpers";

import { Dialog } from "@web/core/dialog/dialog";
import {
    MIN_DIALOG_HEIGHT,
    MIN_DIALOG_WIDTH,
} from "@draggable_and_resizable_wizard/dialog/resizable_dialog";

class Parent extends Component {
    static template = xml`<Dialog title="'Resize me'">content</Dialog>`;
    static components = { Dialog };
}

function dispatchPointer(type, target, x, y) {
    target.dispatchEvent(
        new PointerEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0 })
    );
}

/** Drag the resize handle by (dx, dy) and return the content size before the drag. */
async function dragHandle(dx, dy) {
    const handle = queryOne(".o_dialog_resize_handle");
    const before = queryOne(".modal-content").getBoundingClientRect();
    const handleRect = handle.getBoundingClientRect();
    const x = handleRect.x + handleRect.width / 2;
    const y = handleRect.y + handleRect.height / 2;
    dispatchPointer("pointerdown", handle, x, y);
    dispatchPointer("pointermove", window, x + dx, y + dy);
    dispatchPointer("pointerup", window, x + dx, y + dy);
    await animationFrame();
    return before;
}

function contentSize() {
    const style = queryOne(".modal-content").style;
    return { width: parseFloat(style.width), height: parseFloat(style.height) };
}

test.tags("desktop");
test("dialog is resized from its handle", async () => {
    assignDialogTestEnv();
    await mountWithCleanup(Parent);
    expect(".o_dialog_resize_handle").toHaveCount(1);
    const before = await dragHandle(120, 80);
    // Inline styles are rounded, the bounding rect is not: compare whole pixels.
    const size = contentSize();
    expect(Math.round(size.width)).toBe(Math.round(before.width + 120));
    expect(Math.round(size.height)).toBe(Math.round(before.height + 80));
    expect(".modal-dialog").toHaveClass("o_dialog_resized");
});

test.tags("desktop");
test("dialog cannot be made smaller than the minimum size", async () => {
    assignDialogTestEnv();
    await mountWithCleanup(Parent);
    await dragHandle(-5000, -5000);
    expect(contentSize()).toEqual({ width: MIN_DIALOG_WIDTH, height: MIN_DIALOG_HEIGHT });
});

test.tags("desktop");
test("moving a resized dialog keeps its size", async () => {
    assignDialogTestEnv();
    await mountWithCleanup(Parent);
    await dragHandle(100, 60);
    const resized = contentSize();
    const header = queryOne(".modal-header");
    const headerRect = header.getBoundingClientRect();
    await contains(header).dragAndDrop(".modal-content", {
        position: {
            x: headerRect.x + headerRect.width / 2 + 20,
            y: headerRect.y + headerRect.height / 2 + 30,
        },
    });
    expect(queryOne(".modal-content").style.left).not.toBe("0px");
    expect(contentSize()).toEqual(resized);
});

test.tags("desktop");
test("window resize restores the default size", async () => {
    assignDialogTestEnv();
    await mountWithCleanup(Parent);
    await dragHandle(100, 60);
    await resize();
    await animationFrame();
    expect(queryOne(".modal-content").style.width).toBe("");
    expect(".modal-dialog").not.toHaveClass("o_dialog_resized");
});

test.tags("desktop");
test("fullscreen dialogs have no resize handle", async () => {
    class FullscreenParent extends Component {
        static template = xml`<Dialog fullscreen="true">content</Dialog>`;
        static components = { Dialog };
    }
    assignDialogTestEnv();
    await mountWithCleanup(FullscreenParent);
    expect(".o_dialog").toHaveCount(1);
    expect(".o_dialog_resize_handle").toHaveCount(0);
});
