
$.fn.ImgLazyLoad = function(options) {
    var settings = $.extend({
        mobile: 640,
        qhd: 1680,
        offset: -150,
        time: 200,
    }, options ); 
    var $this = $(this);
    var arrayItems = [];
    var windowSize = window.innerWidth;
    
    $this.each(function( index ) {
        arrayItems.push($(this));
    }); 
    var scrollFlag = false; 
    var time = 10;
    var refreshInterval = setInterval(function(){
        ac_scroll_check();
        if(typeof arrayItems !== 'undefined' && arrayItems.length > 0){
            time = settings.time;
        }else{
            clearInterval(refreshInterval);
        }
    }, time);
    $(window).scroll(ac_scroll_check);
    function ac_scroll_check(){
        if(scrollFlag == false){
			//lock flag
            scrollFlag = true;             
            arrayItems.forEach(function(item, index) {
                if(ac_is_on_screen(item, settings.offset) == true){
                    var imgMedium = item.data('src'),
                    imgSmall = item.data('src-small'), 
                    imgBig = item.data('src-big'),
                    image = imgMedium;
                    if(windowSize < settings.mobile){
                       if (imgSmall != null){
                            image = imgSmall;
                      }
                    }
                    if(windowSize <= settings.qhd && windowSize >= settings.qhd){
                    }
                    if(windowSize > settings.qhd){
                       if (imgBig != null){
                            image = imgBig;
                      }
                    }
                    var isImage = false;
                    if ( item.is( "img" ) ) {
                      isImage = true;
                    }
                    ac_set_image(item, image, isImage);
                    arrayItems.splice(index, 1);
                }         
            }); 
            setTimeout(function() {
                scrollFlag = false;
            }, 100);
        }
    }
    function ac_set_image(element, image, isImage){
        if(isImage){
            element.attr("src", image);
         }else{
            element.css('background-image', 'url(' + image + ')');
         }
    }
    function ac_is_on_screen(elemClass, offset){
        if(!elemClass.length ){
            return false;
        }
        var windowHeight = window.innerHeight;
        var tempScrollTop = $(window).scrollTop();
        var thisTop = elemClass.offset(); 
        var calc = thisTop.top - (windowHeight - offset);
        thisTop = thisTop.top - (windowHeight - offset);
        if(tempScrollTop > thisTop){
            return true;
        }
        return false;
    }
}