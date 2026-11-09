import { afterEach, beforeEach, expect, getFixture, test } from "@odoo/hoot";
import { animationFrame, mockDate } from "@odoo/hoot-mock";
import { Component, EventBus, signal, xml } from "@odoo/owl";
import { destroyApp, mockService, mountWithCleanup, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { session } from "@web/session";
import { BlockUI } from "@web/core/ui/block_ui";
import { ImportBlockUI } from "@base_import/import_block_ui";
import { WebClient } from "@web/webclient/webclient";
import { useThemeDrag } from "@backend_theme_infinito/js/MenuBookmark";
import InfinitoRecentApps from "@backend_theme_infinito/js/recentApps";
import { systrayItem, InfinitoSystrayAdvItem } from "@backend_theme_infinito/js/systray";
import "@backend_theme_infinito/js/loaders";
import "@backend_theme_infinito/js/webclient";
import { Counter } from "@backend_theme_infinito/js/editor_menu";
import { ThemeEditorSidebar } from "@backend_theme_infinito/js/theme_editor_sidebar";

defineMailModels();

beforeEach(() => {
    onRpc("/theme_studio/get_recent_apps", () => []);
});

afterEach(() => {
    document.documentElement.classList.remove("dark-mode");
    document.body.classList.remove("dark-mode");
    localStorage.removeItem("infinito_dark_mode");
});

test("editor access follows admin and personal-edit permissions", () => {
    patchWithCleanup(session, { infinitoCanManageTheme: false, userEdit: false });
    expect(systrayItem.isDisplayed()).toBe(false);
    expect(InfinitoSystrayAdvItem.isDisplayed()).toBe(false);
    session.userEdit = true;
    expect(InfinitoSystrayAdvItem.isDisplayed()).toBe(true);
    expect(systrayItem.isDisplayed()).toBe(false);
    session.infinitoCanManageTheme = true;
    expect(systrayItem.isDisplayed()).toBe(true);
});

test("import loader retains the message and default spinner", async () => {
    patchWithCleanup(session, { loaderClass: "default" });
    await mountWithCleanup(ImportBlockUI, { props: { message: "Importing records" } });
    expect(".o_spinner img").toHaveCount(1);
    expect(".o_message").toHaveText("Importing records");
});

test("custom import loader preserves the message", async () => {
    patchWithCleanup(session, { loaderClass: "rotating" });
    await mountWithCleanup(ImportBlockUI, { props: { message: "Importing records" } });
    expect(".o_spinner .rotating").toHaveCount(1);
    expect(".o_spinner img").toHaveCount(0);
    expect(".o_message").toHaveText("Importing records");
});

test("custom BlockUI respects blocked and unblocked states", async () => {
    patchWithCleanup(session, { loaderClass: "rotating" });
    const component = await mountWithCleanup(BlockUI, { props: { bus: new EventBus() } });
    expect(".o_blockUI").toHaveCount(0);
    component.state.blockState = component.BLOCK_STATES.VISIBLY_BLOCKED;
    component.state.line1 = "Saving records";
    await animationFrame();
    expect(".o_spinner .rotating").toHaveCount(1);
    expect(".o_message").toHaveText("Saving records");
    component.state.blockState = component.BLOCK_STATES.UNBLOCKED;
    await animationFrame();
    expect(".o_blockUI").toHaveCount(0);
});

test("horizontal tray dragging stops when the component is destroyed", async () => {
    class Tray extends Component {
        static template = xml`<div class="drag-tray" t-ref="this.ref" style="position: absolute; left: 10px; top: 20px;"/>`;
        ref = signal.ref();
        setup() {
            useThemeDrag(this.ref, "x");
        }
    }
    await mountWithCleanup(Tray);
    const element = getFixture().querySelector(".drag-tray");
    element.dispatchEvent(new MouseEvent("mousedown", { button: 0, clientX: 30, clientY: 40 }));
    document.dispatchEvent(new MouseEvent("mousemove", { clientX: 60, clientY: 90 }));
    expect(element.style.left).toBe("40px");
    expect(element.style.top).toBe("20px");
    await destroyApp();
    document.dispatchEvent(new MouseEvent("mousemove", { clientX: 100 }));
    expect(element.style.left).toBe("40px");
});

test("recent apps select an existing menu and ignore a missing menu", () => {
    const selected = [];
    const menu = { id: 12 };
    const component = {
        menuService: {
            getMenu: (id) => id === 12 ? menu : undefined,
            selectMenu: (value) => selected.push(value),
        },
    };
    InfinitoRecentApps.prototype.openApp.call(component, { app_id: 12 });
    InfinitoRecentApps.prototype.openApp.call(component, { app_id: 99 });
    expect(selected).toEqual([menu]);
});

test("studio controls apply range limits and units without raw template attributes", () => {
    const container = document.createElement("div");
    container.className = "button_cutomise";
    getFixture().appendChild(container);
    const target = document.createElement("div");
    const editor = Object.create(ThemeEditorSidebar.prototype);
    editor.panelRef = () => getFixture();
    editor.props = { object: { target } };
    editor.state = {};
    editor.renderNewTool({
        name: "width", type: "range", displayName: "Width", unit: "px",
        min: 0, max: 100, alt: [],
    }, 0);
    const input = container.querySelector("input");
    expect(input.value).toBe("0");
    expect(input.min).toBe("0");
    expect(input.max).toBe("100");
    expect(input.hasAttribute("t-att-name")).toBe(false);
    input.value = "25";
    input.dispatchEvent(new Event("change"));
    expect(target.style.width).toBe("25px");
});

test("opening a button sidebar receives props and renders its presets", async () => {
    onRpc("/theme_studio/get_presets", () => ({
        button: [{ name: "Rounded", style: { "border-radius": "8px" } }],
    }));
    const target = document.createElement("button");
    target.className = "btn btn-primary";
    target.dataset.class = "btn-primary";
    getFixture().appendChild(target);
    const sidebar = await mountWithCleanup(ThemeEditorSidebar, {
        props: {
            elem_name: "Button Primary", preset: "button", object: { target },
        },
    });
    await animationFrame();
    expect("#elem_name").toHaveText("Button Primary");
    expect("#presets option").toHaveText("Rounded");
    expect(sidebar.props.object.target).toBe(target);
    const select = getFixture().querySelector("#presets");
    select.dispatchEvent(new Event("change"));
    expect(target.style.borderRadius).toBe("8px");
});

test("overnight dark schedule enables at night and clears stale classes by day", () => {
    patchWithCleanup(session, {
        infinitoDark: true, infinitoDarkMode: "schedule",
        infinitoDarkStart: "19:00", infinitoDarkEnd: "06:00",
    });
    const client = document.createElement("div");
    client.className = "o_web_client";
    getFixture().appendChild(client);
    const context = {};
    mockDate("2026-10-16T23:00:00");
    WebClient.prototype.darkModeCheck.call(context);
    expect(client.classList.contains("dark-mode")).toBe(true);
    expect(localStorage.getItem("infinito_dark_mode")).toBe("1");
    mockDate("2026-10-17T12:00:00");
    WebClient.prototype.darkModeCheck.call(context);
    expect(client.classList.contains("dark-mode")).toBe(false);
    expect(document.documentElement.classList.contains("dark-mode")).toBe(false);
    expect(localStorage.getItem("infinito_dark_mode")).toBe(null);
});


test("advanced settings render and update without signal-only t-model bindings", async () => {
    patchWithCleanup(session, {
        infinitoCanManageTheme: true,
        userEdit: false,
        sidebar: true,
        fullScreenApp: false,
        infinitoDark: false,
        loaderClass: "ring",
    });
    mockService("infinito_advanced_panel", { open() {}, close() {} });
    const component = await mountWithCleanup(Counter);
    const root = getFixture();
    expect(root.querySelector("#sidebarToggler").checked).toBe(true);
    expect(root.querySelector("#userEditToggler").checked).toBe(false);
    expect(root.querySelector("#loader").value).toBe("ring");

    const personal = root.querySelector("#userEditToggler");
    personal.checked = true;
    personal.dispatchEvent(new Event("change", { bubbles: true }));
    expect(component.state.settings.userEdit).toBe(true);

    const fullscreen = root.querySelector("#navbarFullScreenAppToggler");
    fullscreen.checked = true;
    fullscreen.dispatchEvent(new Event("change", { bubbles: true }));
    await animationFrame();
    expect(component.state.settings.fullScreenApp).toBe(true);
    expect(root.querySelector("#sidebarToggler").checked).toBe(false);

    const dark = root.querySelector("#navbarDarkToggler");
    dark.checked = true;
    dark.dispatchEvent(new Event("change", { bubbles: true }));
    await animationFrame();
    expect(component.state.settings.infinitoDark).toBe(true);
    expect(root.querySelector(".dark-switch").style.display).toBe("flex");

    const loader = root.querySelector("#loader");
    loader.value = "bounce";
    loader.dispatchEvent(new Event("change", { bubbles: true }));
    expect(component.state.settings.loaderClass).toBe("bounce");
});
