odoo.define('sidebar_app.SidebarMenu', function (require) {
    "use strict";

    var session = require('web.session');

    //sidebar toggle effect
    $(document).on("click", "#closeSidebar", function(event){
        $("#closeSidebar").hide();
        $("#openSidebar").show();
    });
    $(document).on("click", "#openSidebar", function(event){
        $("#openSidebar").hide();
        $("#closeSidebar").show();
        $("#sidebar_panel").css({'display':'block'});
        let marginLeft = $("#sidebar_panel").css('width');
        let margin_type = session.infinitoRtl ? 'margin-right' : 'margin-left';
        let style = `${margin_type}: calc(${marginLeft} + 25px)`
        $(".o_action_manager").css({'transition':'all .1s linear'});
        $(".o_main_navbar").css({'transition':'all .1s linear'});
        $(".o_action_manager").attr('style', style);

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
        let margin_type = session.infinitoRtl ? 'margin-right' : 'margin-left';
        let style = `${margin_type}: 15px`;
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").attr('style', style);

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
        let margin_type = session.infinitoRtl ? 'margin-right' : 'margin-left';
        let style = `${margin_type}: 15px`;
        $("#sidebar_panel").css({'display':'none'});
        $(".o_action_manager").attr('style', style);
        $("#closeSidebar").hide();
        $("#openSidebar").show();

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