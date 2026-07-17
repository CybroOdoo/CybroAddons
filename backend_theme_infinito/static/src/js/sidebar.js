odoo.define('sidebar_app.SidebarMenu', [], function (require) {
    "use strict";
    document.addEventListener("click", function (event) {

        if (event.target.closest("#closeSidebar")) {
            const closeBtn = document.getElementById("closeSidebar");
            const openBtn = document.getElementById("openSidebar");
            const sidebarPanel = document.getElementById("sidebar_panel");

            if (closeBtn) closeBtn.style.display = "none";
            if (openBtn) openBtn.style.display = "block";
            if (sidebarPanel) sidebarPanel.style.display = "none";

            const actionManager = document.querySelector(".o_action_manager");
            const topHead = document.querySelector(".top_heading");

            if (actionManager) {
                const actionManagerId = actionManager.dataset.id;
                if (actionManagerId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(actionManagerId));
                }
                actionManager.classList.remove("sidebar_margin");
                actionManager.classList.remove("m-sidebar");
            }

            if (topHead) {
                const topHeadId = topHead.dataset.id;
                if (topHeadId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(topHeadId));
                }
                topHead.classList.remove("sidebar_margin");
                topHead.classList.remove("m-sidebar");
            }
        }

        if (event.target.closest("#openSidebar")) {
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
                const actionManagerId = actionManager.dataset.id;
                if (actionManagerId) {
                    document.querySelectorAll("div").forEach(div => div.classList.add(actionManagerId));
                }
                actionManager.classList.add("sidebar_margin");
                if (sidebarPanel && sidebarPanel.classList.contains("m-sidebar")) {
                    actionManager.classList.add("m-sidebar");
                } else {
                    actionManager.classList.remove("m-sidebar");
                }
            }

            if (topHead) {
                const topHeadId = topHead.dataset.id;
                if (topHeadId) {
                    document.querySelectorAll("div").forEach(div => div.classList.add(topHeadId));
                }
                topHead.classList.add("sidebar_margin");
                if (sidebarPanel && sidebarPanel.classList.contains("m-sidebar")) {
                    topHead.classList.add("m-sidebar");
                } else {
                    topHead.classList.remove("m-sidebar");
                }
            }
        }

        if (event.target.closest(".o_web_studio_navbar_item") ||
            event.target.closest(".o-brush-infinito") ||
            event.target.closest("[aria-label*='Studio']") ||
            event.target.closest(".o_studio_action")) {

            const sidebarPanel = document.getElementById("sidebar_panel");
            const closeBtn = document.getElementById("closeSidebar");
            const openBtn = document.getElementById("openSidebar");

            if (sidebarPanel) sidebarPanel.style.display = "none";
            if (closeBtn) closeBtn.style.display = "none";
            if (openBtn) openBtn.style.display = "block";

            const actionManager = document.querySelector(".o_action_manager");
            const topHead = document.querySelector(".top_heading");

            if (actionManager) {
                const actionManagerId = actionManager.dataset.id;
                if (actionManagerId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(actionManagerId));
                }
                actionManager.classList.remove("sidebar_margin");
                actionManager.classList.remove("m-sidebar");
            }

            if (topHead) {
                const topHeadId = topHead.dataset.id;
                if (topHeadId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(topHeadId));
                }
                topHead.classList.remove("sidebar_margin");
                topHead.classList.remove("m-sidebar");
            }
        }

        if (event.target.closest("#menuBookmark a")) {
            const sidebarPanel = document.getElementById("sidebar_panel");
            const closeBtn = document.getElementById("closeSidebar");
            const openBtn = document.getElementById("openSidebar");

            if (sidebarPanel) {
                sidebarPanel.style.display = "none";
                sidebarPanel.classList.remove("show");
            }
            if (closeBtn) closeBtn.style.display = "none";
            if (openBtn) openBtn.style.display = "block";

            const actionManager = document.querySelector(".o_action_manager");
            const topHead = document.querySelector(".top_heading");

            if (actionManager) {
                const actionManagerId = actionManager.dataset.id;
                if (actionManagerId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(actionManagerId));
                }
                actionManager.classList.remove("sidebar_margin");
                actionManager.classList.remove("m-sidebar");
            }

            if (topHead) {
                const topHeadId = topHead.dataset.id;
                if (topHeadId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(topHeadId));
                }
                topHead.classList.remove("sidebar_margin");
                topHead.classList.remove("m-sidebar");
            }
        }

        if (event.target.closest(".sidebar a")) {
            const clickedLink = event.target.closest(".sidebar a");
            const menuItems = document.querySelectorAll(".sidebar a");
            const id = clickedLink.dataset.id;
            const header = document.querySelector("header");

            if (header) {
                // Remove the previously added data-id classes but keep default classes like o_navbar
                menuItems.forEach(item => {
                    const itemId = item.dataset.id;
                    if (itemId) {
                        header.classList.remove(itemId);
                    }
                });
                header.classList.add(id);
                // Ensure the base class is always present
                if (!header.classList.contains("o_navbar")) {
                    header.classList.add("o_navbar");
                }
            }

            menuItems.forEach(item => item.classList.remove("active"));
            clickedLink.classList.add("active");

            const sidebarPanel = document.getElementById("sidebar_panel");
            const closeBtn = document.getElementById("closeSidebar");
            const openBtn = document.getElementById("openSidebar");

            if (sidebarPanel) sidebarPanel.style.display = "none";
            if (closeBtn) closeBtn.style.display = "none";
            if (openBtn) openBtn.style.display = "block";

            const actionManager = document.querySelector(".o_action_manager");
            const topHead = document.querySelector(".top_heading");

            if (actionManager) {
                const actionManagerId = actionManager.dataset.id;
                if (actionManagerId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(actionManagerId));
                }
                actionManager.classList.remove("sidebar_margin");
                actionManager.classList.remove("m-sidebar");
            }

            if (topHead) {
                const topHeadId = topHead.dataset.id;
                if (topHeadId) {
                    document.querySelectorAll("div").forEach(div => div.classList.remove(topHeadId));
                }
                topHead.classList.remove("sidebar_margin");
                topHead.classList.remove("m-sidebar");
            }
        }
    });
});
