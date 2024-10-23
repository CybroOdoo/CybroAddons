// Utility function to apply CSS styles and class modifications
function adjustLayoutOnSidebarToggle(isOpen) {
    const actionManager = $(".o_action_manager");
    const sidebarIcon = $(".side_bar_icon");
    const navbar = $(".o_main_navbar");
    const topHeading = $(".top_heading");

    if (isOpen) {
        $("#sidebar_panel").show();
        if (window.matchMedia("(min-width: 768px)").matches) {
            actionManager.css({ 'margin-left': '200px', 'transition': 'all .1s linear' });
            sidebarIcon.css({ 'margin-left': '200px', 'transition': 'all .1s linear' });
        }
        navbar.addClass("small_nav").addClass(navbar.data("id"));
        actionManager.addClass("sidebar_margin").addClass(actionManager.data("id"));
        topHeading.addClass("sidebar_margin").addClass(topHeading.data("id"));
    } else {
        $("#sidebar_panel").hide();
        actionManager.css({ 'margin-left': '0px' });
        sidebarIcon.css({ 'margin-left': '0px' });
        navbar.removeClass("small_nav").removeClass(navbar.data("id"));
        actionManager.removeClass("sidebar_margin").removeClass(actionManager.data("id"));
        topHeading.removeClass("sidebar_margin").removeClass(topHeading.data("id"));
    }
}

// Toggle sidebar visibility on click
$(document).on("click", "#openSidebar", () => {
    $("#openSidebar").hide();
    $("#closeSidebar").show();
    adjustLayoutOnSidebarToggle(true);
});

$(document).on("click", "#closeSidebar", () => {
    $("#closeSidebar").hide();
    $("#openSidebar").show();
    adjustLayoutOnSidebarToggle(false);
});

// Handle menu item clicks
$(document).on("click", ".sidebar a", function () {
    const $this = $(this);
    const menuItems = $(".sidebar a");

    menuItems.removeClass("active");
    $this.addClass("active");

    // Adjust the header to reflect the active menu
    $("header").removeClass().addClass($this.data("id"));

    // Close sidebar after menu item selection
    adjustLayoutOnSidebarToggle(false);
    $("#closeSidebar").hide();
    $("#openSidebar").show();
});
