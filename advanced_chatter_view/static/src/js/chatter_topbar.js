odoo.define('advanced_chatter_view.chatter_topbar', function (require) {
    'use strict';
    $(document).on("click", "#send_message", function(event){
        $('#chatter_message').removeClass("d-none");
        $('.view').removeClass("d-none");
        $('.cross').removeClass("d-none");
        $('.o_ChatterTopbar_rightSection').removeClass("d-none");
        $('#send_message').hide();
        $('#log_note').hide();
        $('#active').hide();
    });

    $(document).on("click", "#log_note", function(event){
        $('#chatter_note').removeClass("d-none");
        $('.view').removeClass("d-none");
        $('.cross').removeClass("d-none");
        $('.o_ChatterTopbar_rightSection').removeClass("d-none");
        $('#send_message').hide();
        $('#log_note').hide();
        $('#active').hide();
    });

    $(document).on("click", "#active", function(event){
        $('#chatter_activity').removeClass("d-none");
        $('.view').removeClass("d-none");
        $('.cross').removeClass("d-none");
        $('.o_ChatterTopbar_rightSection').removeClass("d-none");
        $('#send_message').hide();
        $('#log_note').hide();
        $('#active').hide();
    });

    $(document).on("click", ".cross", function(event){
        $('#chatter_activity').addClass("d-none");
        $('#chatter_note').addClass("d-none");
        $('#chatter_message').addClass("d-none");
        $('.o_ChatterTopbar_rightSection').addClass("d-none");
        $('.view').addClass("d-none");
        $('.cross').addClass("d-none");
        $('#send_message').show();
        $('#log_note').show();
        $('#active').show();
        $('.chat').addClass("d-none");
    });

    $(document).on("click", "#chatter_message", function(event){
        $('.chat').removeClass("d-none");
    });

    $(document).on("click", "#chatter_note", function(event){
        $('.chat').removeClass("d-none");
    });

});
