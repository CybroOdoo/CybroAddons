 function menuOnClick() {
      show = document.getElementById("top_menu_collapse").classList.contains('show');
      change = document.getElementById("menu-bar").classList.contains('change');
      if(!show && change){
        document.getElementById("menu-bar").classList.remove("change");
      }
      document.getElementById("menu-bar").classList.toggle("change");
    }

var section = $('section').hasClass('header');

    if(section){
    $('header').css('margin-bottom','0');
    }
    else $('header').css('margin-bottom','100px');
