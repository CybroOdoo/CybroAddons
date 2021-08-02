odoo.define('code_backend_theme_enterprise.SidebarMenu', function (require) {
"use strict";

/**
 * This file includes the UserMenu widget defined in Community to add or
 * override actions only available in Enterprise.
 */

    const config = require('web.config');
    const Menu = require("web_enterprise.Menu");
    const SideBar = require("code_backend_theme_enterprise.SideBar");

    Menu.include({
        start() {
            var res = this._super.apply(this, arguments);
            this.sidebar_apps = this.$('.sidebar_panel');
            this._sideBar = new SideBar(this, this.menu_data);
            var sideBar = this._sideBar.appendTo(this.sidebar_apps);

            return res
        },
    });

    //sidebar toggle effect
    $(document).on("click", "#closeSidebar", function(event){
        $("#closeSidebar").hide();
        $("#openSidebar").show();
    });
    $(document).on("click", "#openSidebar", function(event){
        $("#openSidebar").hide();
        $("#closeSidebar").show();
    });
    $(document).on("click", "#openSidebar", function(event){
    console.log('hellooo')
        $("#sidebar_panel").css({'display':'block'});
        $(".o_action_manager").css({'margin-left': '200px','transition':'all .1s linear'});
        $(".top_heading").css({'margin-left': '180px','transition':'all .1s linear'});

        //add class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").addClass(navbar_id);
        navbar.addClass("small_nav");

        //add class in action-manager
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
    $(document).on("click", "#closeSidebar", function(event){
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").css({'margin-left': '0px'});
        $(".top_heading").css({'margin-left': '0px'});

        //remove class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").removeClass(navbar_id);
        navbar.removeClass("small_nav");

        //remove class in action-manager
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

    $(document).on("click", ".sidebar a", function(event){
        var menu = $(".sidebar a");
        var $this = $(this);
        var id = $this.data("id");
        $("header").removeClass().addClass(id);
        menu.removeClass("active");
        $this.addClass("active");

        //sidebar close on menu-item click
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").css({'margin-left': '0px'});
        $(".top_heading").css({'margin-left': '0px'});
        $("#closeSidebar").hide();
        $("#openSidebar").show();

        //remove class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").removeClass(navbar_id);
        navbar.removeClass("small_nav");

        //remove class in action-manager
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
