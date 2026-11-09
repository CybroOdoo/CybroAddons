import { beforeEach, expect, getFixture, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import { mountWithCleanup, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { session } from "@web/session";
import { EditorClientAction } from "@backend_theme_infinito/js/editor_client_action";
import "@backend_theme_infinito/js/checkService";

defineMailModels();

beforeEach(() => {
    patchWithCleanup(session, { infinitoCanManageTheme: true, userEdit: true });
    onRpc("/theme_studio/get_recent_apps", () => []);
    onRpc("/theme_studio/get_presets", () => ({ button: [] }));
    onRpc("/theme_studio/get_current_style", () => []);
});

async function openSettings() {
    getFixture().querySelector("#hamburger").click();
    await animationFrame();
    expect(document.querySelectorAll(".sidebar_simple_editor")).toHaveLength(1);
}

function previewItems() {
    return [...getFixture().querySelectorAll(".preview_area .item[data-class]")];
}

test("editor settings reopen after selecting a preview element", async () => {
    const editor = await mountWithCleanup(EditorClientAction);
    await openSettings();
    previewItems()[0].click();
    await animationFrame();
    expect(document.querySelectorAll(".sidebar_simple_editor")).toHaveLength(0);
    expect(document.querySelectorAll("#theme_editor_sidebar_preset")).toHaveLength(1);
    await openSettings();
    expect(document.querySelectorAll("#theme_editor_sidebar_preset")).toHaveLength(0);
    expect(editor.state.sidebarOpen).toBe(true);
});

test("rapid preview selection keeps only the latest editor sidebar", async () => {
    const editor = await mountWithCleanup(EditorClientAction);
    const items = previewItems();
    items[0].click();
    items[1].click();
    await animationFrame();
    expect(document.querySelectorAll("#theme_editor_sidebar_preset")).toHaveLength(1);
    expect(editor._mountedSidebar.component.props.object.target).toBe(items[1]);
});

test("closing a preset while it mounts leaves no orphan Owl root", async () => {
    const editor = await mountWithCleanup(EditorClientAction);
    previewItems()[0].click();
    editor._closePresetSidebar();
    await animationFrame();
    expect(document.querySelectorAll("#theme_editor_sidebar_preset")).toHaveLength(0);
    expect(editor._mountedSidebar).toBe(null);
});
