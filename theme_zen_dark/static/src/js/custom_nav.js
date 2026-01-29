odoo.define('theme_zen_dark.custom_nav', function (require) {
var publicWidget = require('web.public.widget');
var section = $('section').hasClass('header');
if(section){
    $('header').css('margin-bottom','0');
}
else $('header').css('margin-bottom','100px');
var custom_nav = publicWidget.Widget.extend({
    selector: '#navbar_toggler',
    events: {
        'click #menu-bar': 'menuOnClick',
    },
     menuOnClick: function () {
      show = document.getElementById("top_menu_collapse").classList.contains('show');
      change = document.getElementById("menu-bar").classList.contains('change');
      if(!show && change){
        document.getElementById("menu-bar").classList.remove("change");
      }
      document.getElementById("menu-bar").classList.toggle("change");
     },
});
});

