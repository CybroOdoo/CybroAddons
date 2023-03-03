odoo.define("theme_coffee_shop.theme_coffee_shop_template", function (require) {
  "use strict";
  var ajax = require('web.ajax');

const navicon = document.getElementById('nav-icon');
const navitem = document.getElementById('nav-item');

if(navicon){
    navicon.addEventListener("click",function(e){
      e.preventDefault();
        navitem.classList.toggle('active');
    })
    }

    function functionLike(r) {
      r.classList.toggle("fa-solid");
    }

function fliterclick() {
  var x = document.querySelector(".pr-categories");
  if (x.style.display === "none") {
    x.style.display = "block";
  } else {
    x.style.display = "none";
  }
}


var acc = document.getElementsByClassName("accordion");
var i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    /* Toggle between adding and removing the "active" class,
    to highlight the button that controls the panel */
    this.classList.toggle("active");

    /* Toggle between hiding and showing the active panel */
    var panel = this.nextElementSibling;
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      panel.style.display = "block";
    }
  });
}

const loginPage=document.querySelectorAll("#login-btn");

loginPage.forEach(login=>{
  login.addEventListener('click',e=>{
    e.preventDefault();
    document.querySelector('.login-form-container').classList.toggle('show');
  })
})

document.querySelector(".login-close").onclick=()=>{
  document.querySelector('.login-form-container').classList.toggle('show');
}

});


