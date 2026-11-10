/** @odoo-module **/

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

        [actionManager, topHead].forEach(el => {
            if (!el) return;
            const id = el.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.remove(id));
            el.classList.remove("sidebar_margin", "m-sidebar");
        });
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

        const isMobileSidebar = sidebarPanel && sidebarPanel.classList.contains("m-sidebar");

        [actionManager, topHead].forEach(el => {
            if (!el) return;
            const id = el.dataset.id;
            if (id) document.querySelectorAll("div").forEach(div => div.classList.add(id));
            el.classList.add("sidebar_margin");
            el.classList.toggle("m-sidebar", !!isMobileSidebar);
        });
    }

    //  use the computed style, so it also works when the panel
    // is visible from CSS and has no inline style yet.
    function isSidebarVisible() {
        const panel = document.getElementById("sidebar_panel");
        return !!panel && getComputedStyle(panel).display !== "none";
    }

    // ---- Main click listener ----
    document.addEventListener("click", function (event) {
        const target = event.target;
        const sidebarPanel = document.getElementById("sidebar_panel");

        // 1. Open button (or the apps icon in the navbar)
        if (target.closest("#openSidebar") || target.closest(".oi-apps")) {
            openSidebar();
            return;
        }

        // 2. Close button
        if (target.closest("#closeSidebar")) {
            closeSidebar();
            return;
        }

        // 3. Studio / brush buttons
        if (target.closest(".o_web_studio_navbar_item") ||
            target.closest(".o-brush-infinito") ||
            target.closest("[aria-label*='Studio']") ||
            target.closest(".o_studio_action")) {
            closeSidebar();
            return;
        }

        // 4. Bookmark menu click
        if (target.closest("#menuBookmark a")) {
            closeSidebar();
            return;
        }

        // 5. Sidebar menu item
        if (target.closest(".sidebar a")) {
            const clickedLink = target.closest(".sidebar a");
            const menuItems = document.querySelectorAll(".sidebar a");
            const id = clickedLink.dataset.id;
            const header = document.querySelector("header");

            if (header && id) {
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

        // 6. Click outside the sidebar
        if (isSidebarVisible() && sidebarPanel && !sidebarPanel.contains(target)) {
            closeSidebar();
        }
    }, true);
