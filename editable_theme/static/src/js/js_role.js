$(document).ready(function () {
$('.oe_view_manager_buttons').click(function(){alert()});
    openerp.jsonRpc('/get_css_selected/', 'call', {}).then(function (css_list) {
        /*CSS_LIST = SIDEBAR IMAGE --> TOP IMAGE --> SIDEBAR FONT --> SIDEBAR FONT - PARENT MENU -->
                    TOP BAR FONT --> TOP BAR BACKGROUND COLOR --> SIDE BAR BACKGROUND COLOR -->
        */
//IMAGE
        //SIDEBAR IMAGE
        sidebarBg_IMG_CODED = css_list.substring(0,css_list.indexOf("-->"))
        var sidebarBg_IMG_FORMAT = 'url("data:image/gif;base64,'+ sidebarBg_IMG_CODED +'")'
        $(".oe_leftbar").css("background-image", sidebarBg_IMG_FORMAT);
        //TOP IMAGE
        str_afterFIRST = css_list.substring(css_list.indexOf("-->")+3)
        topBg_IMG_CODED = str_afterFIRST.substring(0,str_afterFIRST.indexOf("-->"))
        var topBg_IMG_FORMAT = 'url("data:image/gif;base64,'+ topBg_IMG_CODED +'")'
        $(".navbar-collapse").css("background-image", topBg_IMG_FORMAT);
//COLOR
        //SIDEBAR FONT
        str_afterSECOND = str_afterFIRST.substring(str_afterFIRST.indexOf("-->")+3)
        sidebarFont_COLOR_CODE = str_afterSECOND.substring(0,str_afterSECOND.indexOf("-->"))
        $(".openerp .oe_menu_text").css("color", sidebarFont_COLOR_CODE);
        //SIDEBAR FONT - PARENT MENU
        str_afterTHIRD = str_afterSECOND.substring(str_afterSECOND.indexOf("-->")+3)
        sidebarFont_COLOR_CODE_parent = str_afterTHIRD.substring(0,str_afterTHIRD.indexOf("-->"))
        $(".openerp .oe_secondary_menu_section").css("color", sidebarFont_COLOR_CODE_parent);
        //TOP BAR FONT
        str_afterFORTH = str_afterTHIRD.substring(str_afterTHIRD.indexOf("-->")+3)
        topBar_Font_COLOR_CODE = str_afterFORTH.substring(0,str_afterFORTH.indexOf("-->"))
        $(".navbar-inverse .navbar-nav > li > a").css("color", topBar_Font_COLOR_CODE);
        //TOP BAR BACKGROUND COLOR
        str_afterFIFTH = str_afterFORTH.substring(str_afterFORTH.indexOf("-->")+3)
        topBar_background_COLOR_CODE = str_afterFIFTH.substring(0,str_afterFIFTH.indexOf("-->"))
        $(".navbar-collapse.collapse").css("background-color", topBar_background_COLOR_CODE);
        //SIDE BAR BACKGROUND COLOR
        str_afterSIXTH = str_afterFIFTH.substring(str_afterFIFTH.indexOf("-->")+3)
        sideBar_background_COLOR_CODE = str_afterSIXTH.substring(0,str_afterSIXTH.indexOf("-->"))
        $(".oe_leftbar").css("background-color", sideBar_background_COLOR_CODE);
//FONT STYLE
        str_afterSEVENTH = str_afterSIXTH.substring(str_afterSIXTH.indexOf("-->")+3)
        sideBar_background_COLOR_CODE = str_afterSEVENTH.substring(0,str_afterSEVENTH.indexOf("-->"))
        console.log(sideBar_background_COLOR_CODE)
        //SIDE
        $(".oe_leftbar").css("font-family", sideBar_background_COLOR_CODE);
        $("a").css("font-family", sideBar_background_COLOR_CODE);
    });
})