odoo.define('sidebar_app.SidebarMenu', [], function (require) {
    "use strict";

    // ---- Helper functions to open/close the sidebar ----
    function closeSidebar() {
        const closeBtn = document.getElementById("closeSidebar");
        const openBtn = document.getElementById("openSidebar");
        const sidebarPanel = document.getElementById("sidebar_panel");

        if (closeBtn) closeBtn.style.display = "none";
        if (openBtn) openBtn.style.display = "block";
        if (sidebarPanel) sidebarPanel.style.display = "none";

        const actionManager = document.querySelector(".o_action_manager");
        const topHead = document.querySelector(".top_heading");

        if (actionManager) {
            const id = actionManager.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.remove(id));
            actionManager.classList.remove("sidebar_margin", "m-sidebar");
        }
        if (topHead) {
            const id = topHead.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.remove(id));
            topHead.classList.remove("sidebar_margin", "m-sidebar");
        }
    }

    function openSidebar() {
        const openBtn = document.getElementById("openSidebar");
        const closeBtn = document.getElementById("closeSidebar");
        const sidebarPanel = document.getElementById("sidebar_panel");

        if (openBtn) openBtn.style.display = "none";
        if (closeBtn) closeBtn.style.display = "block";
        if (sidebarPanel) sidebarPanel.style.display = "block";

        const actionManager = document.querySelector(".o_action_manager");
        const mainNavbar = document.querySelector(".o_main_navbar");
        const topHead = document.querySelector(".top_heading");

        [actionManager, mainNavbar].forEach(el => {
            if (el) el.style.transition = "all .1s linear";
        });

        if (actionManager) {
            const id = actionManager.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.add(id));
            actionManager.classList.add("sidebar_margin");
            if (sidebarPanel && sidebarPanel.classList.contains("m-sidebar")) {
                actionManager.classList.add("m-sidebar");
            } else {
                actionManager.classList.remove("m-sidebar");
            }
        }
        if (topHead) {
            const id = topHead.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.add(id));
            topHead.classList.add("sidebar_margin");
            if (sidebarPanel && sidebarPanel.classList.contains("m-sidebar")) {
                topHead.classList.add("m-sidebar");
            } else {
                topHead.classList.remove("m-sidebar");
            }
        }
    }

    function isSidebarVisible() {
        const panel = document.getElementById("sidebar_panel");
        return panel && panel.style.display === "block";
    }

    // ---- Main click listener ----
    document.addEventListener("click", function (event) {
        const target = event.target;
        const sidebarPanel = document.getElementById("sidebar_panel");

        // ---- 1. Detect Open button (now includes .oi-apps) ----
        if (target.closest("#openSidebar") || target.closest(".oi-apps")) {
            openSidebar();
            return; // prevent any other handler for this click
        }

        // ---- 2. Detect Close button ----
        if (target.closest("#closeSidebar")) {
            closeSidebar();
            return;
        }

        // ---- 3. Studio / brush / etc. ----
        if (target.closest(".o_web_studio_navbar_item") ||
            target.closest(".o-brush-infinito") ||
            target.closest("[aria-label*='Studio']") ||
            target.closest(".o_studio_action")) {
            closeSidebar();
            return;
        }

        // ---- 4. Bookmark menu click ----
        if (target.closest("#menuBookmark a")) {
            closeSidebar();
            return;
        }

        // ---- 5. Sidebar menu item ----
        if (target.closest(".sidebar a")) {
            const clickedLink = target.closest(".sidebar a");
            const menuItems = document.querySelectorAll(".sidebar a");
            const id = clickedLink.dataset.id;
            const header = document.querySelector("header");

            if (header) {
                // Remove all previously added data-id classes
                menuItems.forEach(item => {
                    const itemId = item.dataset.id;
                    if (itemId) header.classList.remove(itemId);
                });
                header.classList.add(id);
                if (!header.classList.contains("o_navbar")) {
                    header.classList.add("o_navbar");
                }
            }

            menuItems.forEach(item => item.classList.remove("active"));
            clickedLink.classList.add("active");

            closeSidebar();
            return;
        }

        // ---- 6. Outside‑click detection (NEW) ----
        if (isSidebarVisible()) {
            // If click is outside the sidebar panel and NOT on the open button (already handled above),
            // close the sidebar.
            const isInside = sidebarPanel && sidebarPanel.contains(target);
            // Also ignore clicks on the open button (already returned earlier, but just in case)
            const isOpenButton = target.closest("#openSidebar") || target.closest(".oi-apps");
            if (!isInside && !isOpenButton) {
                closeSidebar();
            }
        }
    });
});