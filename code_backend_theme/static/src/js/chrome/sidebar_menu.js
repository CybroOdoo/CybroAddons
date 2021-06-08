odoo.define('code_backend_theme.SidebarMenu', function (require) {
    "use strict";

    const config = require("web.config");
    const Menu = require("web.Menu");
    const SideBar = require("code_backend_theme.SideBar");

    Menu.include({
        start() {
            var res = this._super.apply(this, arguments);
            this.sidebar_apps = this.$('.sidebar_panel');
            this._sideBar = new SideBar(this, this.menu_data);
            var sideBar = this._sideBar.appendTo(this.sidebar_apps);

            return res, sideBar
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
        $("#sidebar_panel").css({'display':'block'});
        $(".o_action_manager").css({'margin-left': '200px','transition':'all .1s linear'});
        $(".top_heading").css({'margin-left': '180px','transition':'all .1s linear'});

        //add class in navbar
        var navbar = $(".o_main_navbar");
        var navbar_id = navbar.data("id");
        $("nav").addClass(navbar_id);
        navbar.addClass("small_nav");
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
    });
});