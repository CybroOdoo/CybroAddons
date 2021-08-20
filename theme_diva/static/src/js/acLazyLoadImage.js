//lazyload

// how to use
//$('.imageLazyLoad').ImgLazyLoad({mobile: "", qhd:"", offset:"", time:""});
$.fn.ImgLazyLoad = function(options) {
    var settings = $.extend({
        // These are the defaults settings.
        mobile: 640,  
        qhd: 1680,
        offset: -150,
        time: 200,
    }, options ); 
    var $this = $(this);
    var arrayItems = [];
    var windowSize = window.innerWidth;
    
    // elements to array
    $this.each(function( index ) {
        arrayItems.push($(this));
    }); 
    var scrollFlag = false; 
    var time = 10;
    //check in time interval
    var refreshInterval = setInterval(function(){
        ac_scroll_check();
        if(typeof arrayItems !== 'undefined' && arrayItems.length > 0){
            time = settings.time;
        }else{
            clearInterval(refreshInterval);
        }
    }, time);
    // on scroll
    $(window).scroll(ac_scroll_check);
    // main function
    function ac_scroll_check(){
        if(scrollFlag == false){
			//lock flag
            scrollFlag = true;             
            arrayItems.forEach(function(item, index) {
                if(ac_is_on_screen(item, settings.offset) == true){
                    //load image url
                    var imgMedium = item.data('src'), 
                    imgSmall = item.data('src-small'), 
                    imgBig = item.data('src-big'),
                    image = imgMedium;
                    //if is mobile
                    if(windowSize < settings.mobile){
                       //console.log('mobile view');
                       if (imgSmall != null){
                            image = imgSmall;
                      }
                    }
                    //if is desktop
                    if(windowSize <= settings.qhd && windowSize >= settings.qhd){
                       //console.log('normal view');
                    }
                    //if is QHD
                    if(windowSize > settings.qhd){
                       //console.log('qhd view');
                       if (imgBig != null){
                            image = imgBig;
                      }
                    }
                    // if element is image
                    var isImage = false;
                    if ( item.is( "img" ) ) {
                      isImage = true;
                    }
                    ac_set_image(item, image, isImage);
                    //image loader remove from array
                    arrayItems.splice(index, 1);
                }         
            }); 
            setTimeout(function() {
                //release flag
                scrollFlag = false;
            }, 100);
        }
    }
    //set image
    function ac_set_image(element, image, isImage){
        if(isImage){
            element.attr("src", image);
         }else{
            element.css('background-image', 'url(' + image + ')');
         }
    }
    //check if element is on screen function
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