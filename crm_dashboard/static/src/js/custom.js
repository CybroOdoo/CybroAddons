odoo.define('crm_dashboard.custom', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var manager = false;
    rpc.query({
        model: "crm.lead",
        method: "check_user_group",
    })
    .then(function (res) {
        manager = res;
    });

    $(document).on("mouseenter", ".dashboard_main_section", function(event){
        if (manager) {
            var percentage_crm = $('#percentage_crm').val();
            var gauge = new Gauge(document.getElementById("gauge"));
            gauge.value(percentage_crm);
            $('#country_revenue_table').columnHeatmap({
                columns: [1],
                inverse:true,
            });
            $('#country_count_table').columnHeatmap({
                columns: [1],
                inverse:true,
            });
            $('#salesperson_revenue_table').columnHeatmap({
                columns: [1],
                inverse:true,
            });
        }
    });
//    $(document).on("click", "#view_lost_dashboard", function(event){
//        $(".dashboard_main_section").css({'display':'none'});
//        $("#dashboard_sub_section").css({'display':'block'});
//    });
//    function BreadcrumbSubDash(){
//        $(".dashboard_main_section").css({'display':'block'});
//        $("#dashboard_sub_section").css({'display':'none'});
//    };
});