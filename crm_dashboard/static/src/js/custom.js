$(document).on("click", "#view_lost_dashboard", function(event){
    $(".dashboard_main_section").css({'display':'none'});
    $("#dashboard_sub_section").css({'display':'block'});
});
function BreadcrumbSubDash(){
    $(".dashboard_main_section").css({'display':'block'});
    $("#dashboard_sub_section").css({'display':'none'});
};