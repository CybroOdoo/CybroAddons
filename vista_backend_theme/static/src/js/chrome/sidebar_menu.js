odoo.define('vista_backend_theme.SidebarMenu', function (require) {
    "use strict";

    const config = require("web.config");
    const Menu = require("web.Menu");
    const SideBar = require("vista_backend_theme.SideBar");

    Menu.include({
        start() {
            var res = this._super.apply(this, arguments);
            this.sidebar_apps = this.$('.sidebar_panel');
            this._sideBar = new SideBar(this, this.menu_data);
            var sideBar = this._sideBar.appendTo(this.sidebar_apps);

            return res, sideBar
        },
    });

    function showSidebar(){
        $("#sidebar_panel").css({'display':'block'});
        $(".o_action_manager").css({'margin-left': '90px','transition':'all .1s linear'});
        $(".top_heading").css({'margin-left': '78px','transition':'all .1s linear'});
        $("#dotsWhite").toggleClass("d-block d-none");
        $("#dotsPrimary").toggleClass("d-block d-none");
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
    }

    function hideSidebar(){
     $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").css({'margin-left': '0px'});
        $(".top_heading").css({'margin-left': '0px'});
        $("#dotsWhite").toggleClass("d-block d-none");
        $("#dotsPrimary").toggleClass("d-block d-none");
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
    }

    var showBar = false;

    $(document).on("click", "#triggerSidebar", function(event){

        if(showBar){
            hideSidebar();
        }else{
            showSidebar();
        }
         $("#triggerSidebar").toggleClass('c_sidebar_active c_sidebar_passive');
         $('#dotsMenuContainer').toggleClass('c_dots_menu c_dots_menu_toggled');
         showBar = !showBar;
    });

  /*  $(document).on("click", ".sidebar a", function(event){
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
    });*/
});