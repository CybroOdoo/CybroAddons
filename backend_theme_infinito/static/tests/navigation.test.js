import { beforeEach, expect, getFixture, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import {
    contains, defineMenus, mountWithCleanup, onRpc, patchWithCleanup,
} from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { session } from "@web/session";
import { NavBar } from "@web/webclient/navbar/navbar";
import MenuBookmark from "@backend_theme_infinito/js/MenuBookmark";
import "@backend_theme_infinito/js/navbar";

defineMailModels();

beforeEach(() => {
    onRpc("/theme_studio/get_recent_apps", () => []);
    patchWithCleanup(session, {
        sidebar: true, sidebarIcon: true, sidebarName: true,
        sidebarCompany: false, sidebarUser: false, fullScreenApp: false,
        infinitoCanManageTheme: false, userEdit: false, infinitoRtl: false,
    });
    defineMenus([{ id: 1, name: "Sales" }, { id: 2, name: "Inventory" }]);
});

async function mountNavbar() {
    const main = document.createElement("div");
    main.className = "o_action_manager";
    getFixture().append(main);
    return mountWithCleanup(NavBar);
}

async function assertSidebar(open) {
    await animationFrame();
    const root = getFixture();
    expect(root.querySelector("#sidebar_panel").style.display).toBe(open ? "block" : "none");
    expect(root.querySelector(".o_action_manager").classList.contains("sidebar_margin")).toBe(open);
}

test.tags("desktop");
test("desktop sidebar selection closes state and reopens with one click", async () => {
    const navbar = await mountNavbar();
    let selected;
    patchWithCleanup(navbar.menuService, { selectMenu: (menu) => { selected = menu.id; } });
    // Keep the menu selection RPC local to this test.
    onRpc("/theme_studio/add_recent_app", () => true);
    await contains("#openSidebar").click();
    await assertSidebar(true);
    await contains("#sidebar_panel a[data-menu-id='1']").click();
    expect(selected).toBe(1);
    expect(navbar.state.sidebarOpen).toBe(false);
    await assertSidebar(false);
    await contains("#openSidebar").click();
    await assertSidebar(true);
});

test.tags("desktop");
test("outside click and close button each permit a single-click reopen", async () => {
    const navbar = await mountNavbar();
    await contains("#openSidebar").click();
    await contains(".o_action_manager").click();
    expect(navbar.state.sidebarOpen).toBe(false);
    await assertSidebar(false);
    await contains("#openSidebar").click();
    await assertSidebar(true);
    await contains("#closeSidebar").click();
    await assertSidebar(false);
    await contains("#openSidebar").click();
    await assertSidebar(true);
});

test.tags("desktop");
test("RTL compact sidebar keeps its layout classes across reopen", async () => {
    patchWithCleanup(session, { infinitoRtl: true, sidebarName: false });
    await mountNavbar();
    await contains("#openSidebar").click();
    expect("#sidebar_panel").toHaveClass("infinito-rtl m-sidebar");
    expect(".o_action_manager").toHaveClass("sidebar_margin m-sidebar");
    await contains(".o_action_manager").click();
    await contains("#openSidebar").click();
    await assertSidebar(true);
    expect(".o_action_manager").toHaveClass("m-sidebar");
});

test.tags("desktop");
test("full-screen menu toggles and restores the action area", async () => {
    patchWithCleanup(session, { sidebar: false, fullScreenApp: true });
    await mountNavbar();
    await contains("a.full").click();
    expect(".fullscreen-menu").toHaveClass("show");
    expect(getFixture().querySelector(".o_action_manager").style.display).toBe("none");
    await contains("a.full").click();
    expect(".fullscreen-menu").not.toHaveClass("show");
    expect(getFixture().querySelector(".o_action_manager").style.display).toBe("");
});

test.tags("desktop");
test("bookmark navigation closes the sidebar without desynchronizing its toggle", async () => {
    patchWithCleanup(session, { infinitoMenuBookmarks: [
        { name: "Sales", short_name: "SA", url: "/odoo/sales" },
    ] });
    const navbar = await mountNavbar();
    await mountWithCleanup(MenuBookmark);
    const link = getFixture().querySelector("#menuBookmark a");
    // Keep this navigation in the test document while exercising the real click listener.
    link.addEventListener("click", (ev) => ev.preventDefault());
    expect(link.getAttribute("href")).toBe("/odoo/sales");
    await contains("#openSidebar").click();
    link.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    expect(navbar.state.sidebarOpen).toBe(false);
    await assertSidebar(false);
    await contains("#openSidebar").click();
    await assertSidebar(true);
});
