import { registry } from "@web/core/registry";

/**
 * Tour test for responsive_web:
 * 1. Checks that the custom app drawer toggle button is rendered in the navbar.
 * 2. Clicks the custom app drawer button to open the responsive drawer client action.
 * 3. Verifies that the responsive app drawer and app menu items are rendered.
 * 4. Triggers global menu search by typing into the drawer / search input.
 * 5. Verifies that the search modal and results are rendered.
 * 6. Closes the search modal.
 */
registry.category("web_tour.tours").add("responsive_web_tour", {
    steps: () => [
        {
            content: "Check that the custom navbar button exists",
            trigger: ".o_main_navbar .custom_navbar_button",
            run: "click",
        },
        {
            content: "Verify that the responsive app drawer view is displayed",
            trigger: ".dashboard_main.o_web_responsive",
        },
        {
            content: "Verify that app icons are rendered in the app drawer",
            trigger: ".nav-container .app-menu",
        },
        {
            content: "Trigger global menu search by typing a key",
            trigger: ".dashboard_main.o_web_responsive",
            run: function () {
                window.dispatchEvent(new KeyboardEvent("keydown", { key: "a", bubbles: true }));
            },
        },
        {
            content: "Verify search modal is open",
            trigger: ".responsive-modal-content .responsive_search_input",
            run: "edit Discuss",
        },
        {
            content: "Close the search modal",
            trigger: ".modal-header button",
            run: "click",
        },
        {
            content: "Verify returning to app drawer",
            trigger: ".nav-container .app-menu",
        },
    ],
});
