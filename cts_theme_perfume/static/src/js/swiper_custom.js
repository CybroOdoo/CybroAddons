  // swiper js code start
  var galleryTop = new Swiper('.gallery-top', {
    spaceBetween: 0,
    
    navigation: {
      nextEl: '.navigationHide',
      prevEl: '.navigationHide',
    },
    // autoplay: true,
     loop: true,
    loopedSlides: 4
  });
  var galleryThumbs = new Swiper('.gallery-thumbs', {
    spaceBetween: 0,
    centeredSlides: true,
    slidesPerView: 4,
    touchRatio: 0.2,
    slideToClickedSlide: true,
    loop: true,
    loopedSlides: 4
  });
  galleryTop.controller.control = galleryThumbs;
  galleryThumbs.controller.control = galleryTop;
  // swiper js code end