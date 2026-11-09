import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("hide_menu_user_favorites_and_app_order", {
    steps: () => [
        // Star the page currently displayed (Settings > Users).
        { trigger: ".o_list_view" },
        { trigger: ".o_hide_menu_favorite_toggle", run: "click" },
        { trigger: ".o_hide_menu_favorite_current button.btn-primary", run: "click" },
        { trigger: ".o_hide_menu_favorite_entry[data-menu-xmlid='base.menu_action_res_users']" },
        // Find another menu through the search box and star it.
        { trigger: ".o_hide_menu_favorite_dropdown input[type=search]", run: "edit Companies" },
        {
            trigger: ".o_hide_menu_favorite_entry[data-menu-xmlid='base.menu_action_res_company_form'] .o_hide_menu_favorite_star",
            run: "click",
        },
        {
            trigger:
                ".o_hide_menu_favorite_entry[data-menu-xmlid='base.menu_action_res_company_form'] .o_hide_menu_favorite_star .oi-filled",
        },
        { trigger: ".o_hide_menu_favorite_dropdown input[type=search]", run: "clear" },
        { trigger: ".o_hide_menu_favorite_section_title:contains(Settings)" },
        // Reorder the apps from the user menu.
        { trigger: "body", run: "press Escape" },
        { trigger: ".o_user_menu", run: "click" },
        { trigger: ".dropdown-item[data-menu='hide_menu_user.arrange_apps']", run: "click" },
        { trigger: ".o_hide_menu_app_order_item:eq(0) button[aria-label='Move down']", run: "click" },
        { trigger: ".modal-footer .btn-primary", run: "click" },
        { trigger: ".o_notification:contains(Your app order has been saved)" },
    ],
});
