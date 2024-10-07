odoo.define('sidebar_app.SidebarMenu', [], function (require) {
    "use strict";
    // Importing session module
    var session = require('web.session');

    /**
     * Function to handle sidebar toggle effect when close button is clicked
     */
    $(document).on("click", "#closeSidebar", function(event){
        $("#closeSidebar").hide();
        $("#openSidebar").show();
    });
    /**
     * Function to handle sidebar toggle effect when open button is clicked
     */
    $(document).on("click", "#openSidebar", function(event){
        $("#openSidebar").hide();
        $("#closeSidebar").show();
        $("#sidebar_panel").css({'display':'block'});
        let marginLeft = $("#sidebar_panel").css('width');
        // Transition effects for action manager and main navbar
        $(".o_action_manager").css({'transition':'all .1s linear'});
        $(".o_main_navbar").css({'transition':'all .1s linear'});

        // Adding class for sidebar margin in action manager and top heading
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").addClass(action_manager_id);
        action_manager.addClass("sidebar_margin");

        //add class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").addClass(top_head_id);
        top_head.addClass("sidebar_margin");
    });
    /**
     * Function to handle sidebar toggle effect when close button is clicked again
     */
    $(document).on("click", "#closeSidebar", function(event){

        $("#sidebar_panel").css({'display':'none'});

        // Removing class for sidebar margin in action manager and top heading
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").removeClass(action_manager_id);
        action_manager.removeClass("sidebar_margin");

        //remove class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").removeClass(top_head_id);
        top_head.removeClass("sidebar_margin");
    });
    /**
     * Function to handle active state of sidebar menu items
     */
    $(document).on("click", ".sidebar a", function(event){
        var menu = $(".sidebar a");
        var $this = $(this);
        var id = $this.data("id");
        $("header").removeClass().addClass(id);
        menu.removeClass("active");
        $this.addClass("active");

        // Closing sidebar when menu item is clicked

        $("#sidebar_panel").css({'display':'none'});
        $("#closeSidebar").hide();
        $("#openSidebar").show();

        // Removing class for sidebar margin in action manager and top heading
        var action_manager = $(".o_action_manager");
        var action_manager_id = action_manager.data("id");
        $("div").removeClass(action_manager_id);
        action_manager.removeClass("sidebar_margin");

        //remove class in top_heading
        var top_head = $(".top_heading");
        var top_head_id = top_head.data("id");
        $("div").removeClass(top_head_id);
        top_head.removeClass("sidebar_margin");
    });
});
