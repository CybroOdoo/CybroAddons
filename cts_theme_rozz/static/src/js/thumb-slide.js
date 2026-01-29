var bigimage = $("#big");
var thumbs = $("#thumbs");
  //var totalslides = 10;
var syncedSecondary = true;

bigimage
  .owlCarousel({
  items: 1,
  slideSpeed: 2000,
  nav: false,
  autoplay: true,
  dots: false,
  loop: true,
  responsiveRefreshRate: 200,
})

.on("changed.owl.carousel", syncPosition);

thumbs
  .on("initialized.owl.carousel", function() {
  thumbs
  .find(".owl-item")
  .eq(0)
  .addClass("current");
})
.owlCarousel({
  items: 4,
  margin: 20,
  dots: false,
  nav: false,
  smartSpeed: 200,
  slideSpeed: 500,
  slideBy: 4,
  responsiveRefreshRate: 100,
  responsive:{
    0:{
      items:2,
    },
    600:{
      items:2,
    },
    1000:{
      items:4,
    }
  }
})

.on("changed.owl.carousel", syncPosition2);

function syncPosition(el) {
  //if loop is set to false, then you have to uncomment the next line
  //var current = el.item.index;

  //to disable loop, comment this block
  var count = el.item.count - 1;
  var current = Math.round(el.item.index - el.item.count / 2 - 0.5);

  if (current < 0) {
    current = count;
  }
  if (current > count) {
    current = 0;
  }
  //to this
  thumbs
    .find(".owl-item")
    .removeClass("current")
    .eq(current)
    .addClass("current");
  var onscreen = thumbs.find(".owl-item.active").length - 1;
  var start = thumbs
  .find(".owl-item.active")
  .first()
  .index();
  var end = thumbs
  .find(".owl-item.active")
  .last()
  .index();

  if (current > end) {
    thumbs.data("owl.carousel").to(current, 100, true);
  }
  if (current < start) {
    thumbs.data("owl.carousel").to(current - onscreen, 100, true);
  }
}

function syncPosition2(el) {
  if (syncedSecondary) {
    var number = el.item.index;
    bigimage.data("owl.carousel").to(number, 100, true);
  }
}

thumbs.on("click", ".owl-item", function(e) {
  e.preventDefault();
  var number = $(this).index();
  bigimage.data("owl.carousel").to(number, 300, true);
});