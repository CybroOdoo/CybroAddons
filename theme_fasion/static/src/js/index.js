$(document).ready(function () {
      $('.image_slider').slick({
        asNavFor: '.image_discription',
        arrows: false,
        slidesToShow: 1,
  slidesToScroll: 1,
  centerMode: true,
  variableWidth: true
      });


      $('.image_discription').slick({
  slidesToShow: 1,
  slidesToScroll: 3,
  asNavFor: '.image_slider',
  dots: false,
  // centerMode: true,
  // focusOnSelect: true,
  arrows:false,
});

      // $('.image_discription').slick(
      //   {
      //     asNavFor: '.image_slider',
      //     appendArrows: $('.imgdics_button'),
      //     nextArrow: '<button type="button" class="slick-next"></button>',
      //     prevArrow: '<button type="button" class="slick-prev"></button>',
      //   }

      // );

    });
