odoo.define('code_backend_theme_enterprise.SideBar', [], function (require) {
    "use strict";
    // Sidebar toggle effect
    $(document).on("click", "#closeSidebar", function(event){
        $("#closeSidebar").hide();
        $("#openSidebar").show();
    });
    $(document).on("click", "#openSidebar", function(event){
        $("#openSidebar").hide();
        $("#closeSidebar").show();
    });
    $(document).on("click", "#openSidebar", function(event){
        $("#sidebar_panel").css({'display':'block'});
        if (window.matchMedia("(min-width: 768px)").matches) {
            $(".o_action_manager").css({'margin-left': '200px','transition':'all .1s linear'});
            $(".side_bar_icon").css({'margin-left': '200px','transition':'all .1s linear'});
        } else {
            $(".o_action_manager").css({'transition':'all .1s linear'});
            $(".side_bar_icon").css({'transition':'all .1s linear'});
        }
        // Add class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").addClass(navbar_id);
        navbar.addClass("small_nav");
        // Add class in action-manager
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").addClass(action_manager_id);
        action_manager.addClass("sidebar_margin");
        // Add class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").addClass(top_head_id);
        top_head.addClass("sidebar_margin");
    });
    $(document).on("click", "#closeSidebar", function(event){
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").css({'margin-left': '0px'});
        $(".side_bar_icon").css({'margin-left': '0px'});
        // Remove class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").removeClass(navbar_id);
        navbar.removeClass("small_nav");
        // Remove class in action-manager
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").removeClass(action_manager_id);
        action_manager.removeClass("sidebar_margin");
        // Remove class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").removeClass(top_head_id);
        top_head.removeClass("sidebar_margin");
    });
    $(document).on("click", ".sidebar a", function(event){
        var menu = $(".sidebar a");
        var $this = $(this);
        var id = $this.data("id");
        $("header").removeClass().addClass(id);
        menu.removeClass("active");
        $this.addClass("active");
        // Sidebar close on menu-item click
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").css({'margin-left': '0px'});
        $(".side_bar_icon").css({'margin-left': '0px'});
        $("#closeSidebar").hide();
        $("#openSidebar").show();
        // Remove class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").removeClass(navbar_id);
        navbar.removeClass("small_nav");
        // Remove class in action-manager
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").removeClass(action_manager_id);
        action_manager.removeClass("sidebar_margin");
        // Remove class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").removeClass(top_head_id);
        top_head.removeClass("sidebar_margin");
    });
});
