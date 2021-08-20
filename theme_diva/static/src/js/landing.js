odoo.define('theme_diva.theme_diva', function (require) {
	"use strict";
	 $(document).ready(function () {
            $(".img_lazy").ImgLazyLoad({
                mobile: "640",
                qhd: "1680",
                offset: "-150",
                time: "550",
                animateOut: 'img_lazy'
            });
             <!-- scroll reveal -->

//            ScrollReveal().reveal('.bg');
//            ScrollReveal().reveal('.bg_delay', { delay: 500 });
//            ScrollReveal().reveal('.icon', { delay: 750 });
//            ScrollReveal().reveal('.tagline', { delay: 1000, scale: 1, reset: true, origin: 'top'});
//            ScrollReveal().reveal('.subline', { delay: 1500, scale: 1, reset: true, origin: 'top'});
//            ScrollReveal().reveal('.punchline', { delay: 2000 });
//            ScrollReveal().reveal('.headline', { duration: 2000 });
//            ScrollReveal().reveal('.widget', { interval: 600 });
//            ScrollReveal().reveal('.tile', { interval: 500, reset: true });
//            ScrollReveal().reveal('.footer_duration', { interval: 50, reset: true });

    <!-- email validation -->

            function myFunction() {
                var email;
                email = document.getElementById("textEmail").value;
                var reg = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
                if (reg.test(textEmail.value) == false) {
                    document.getElementById("demo").style.color = "#535353";
                    document.getElementById("demo").style.padding = "8px 0px";
                    document.getElementById("demo").innerHTML = " The email you entered isn't valid.." + email;
                return false;
                } else {
                    document.getElementById("demo").style.color = "#50449c";
                    document.getElementById("demo").style.padding = "8px 0px";
                    document.getElementById("demo").innerHTML = "<i class='fas fa-hand-point-right'></i> <strong>  WOOHOO</strong> You subscribed successfully.. " + email;
                }
                return true;
            }


            $(window).resize(function() {
                if ($(this).width() < 1024) {
                    $('.widget').hide();
                }
                else {
                    $('.widget').show();
                }
            });
    });
});












