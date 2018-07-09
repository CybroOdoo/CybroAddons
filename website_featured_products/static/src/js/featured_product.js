$(document).on('ready', function() {
      $(".center").slick({
        dots: false,
        infinite: true,
        slidesToShow: 5,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 1000,
        prevArrow: '',
        nextArrow: '',
      });
    });