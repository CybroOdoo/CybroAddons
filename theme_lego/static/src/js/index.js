
    $(document).ready(function () {
      $("#slider").owlCarousel(
        {
          items: 1,
          loop: true,
          margin: 30,
          stagePadding: 30,
          smartSpeed: 450,
          autoplay: true,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 1000,
          autoplayHoverPause: true,
          dots: true,
          nav: true,
          navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>']
        }
      );
    });
    function counter() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item) {
        $(item).find('span').text(index + 1);
      });
    }



    $(document).ready(function () {
      $("#owl-theme2").owlCarousel(
        {
          items: 1,
          loop: true,
          margin: 30,
          stagePadding: 30,
          smartSpeed: 450,
          autoplay: true,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 1000,
          autoplayHoverPause: true,
          dots: true,
          nav: true,
          navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>']
        }
      );
    });
    function counter() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item) {
        $(item).find('span').text(index + 1);
      });
    }



