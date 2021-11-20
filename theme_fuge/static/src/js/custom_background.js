var div = $('div').hasClass('homepage');

    if(div){
    $('.navbar').css('background-color','rgb(114, 89, 89)');
    $('.navbar').css('z-index','0');
    $('.banner').css('margin-bottom','0');
    }
    else {
     $('.navbar').css('background-color','rgb(114, 89, 89)');
     $('.banner').css('margin-bottom','100px');
     }

