odoo.define('backend_theme_infinito.timepicker', function (require) {
    "use strict";
var session = require('web.session');
var Widget = require('backend_theme_infinito.ThemeStudioWidget');


var TimePicker = Widget.extend({
    template: 'theme_advance',
    events: {
            'click #tp-set': 'set',
            'click #tp-close': 'close',
    },
    init: function (parent){
        this._super.apply(this, arguments);
        this.parent = parent;
    },
    start:function(){
        this._super.apply(...arguments)
        this.hhr = this.$el.find('#tp-hr')[0];
        this.hmin = this.$el.find('#tp-min')[0];
        for (let segment of ["hr", "min"]) {
            let up = this.$el.find(`#tp-${segment} .tp-up`)[0];
            let down = this.$el.find(`#tp-${segment} .tp-down`)[0];
            this["h"+segment] = this.$el.find(`#tp-${segment} .tp-val`)[0];
            up.onmousedown = () => { this.spin(true, segment); };
            down.onmousedown = () => { this.spin(false, segment); };
            up.onmouseup = () => { this.spin(null); };
            down.onmouseup = () => { this.spin(null); };
            up.onmouseleave = () => { this.spin(null); };
            down.onmouseleave = () => { this.spin(null); };
        }
        this.timer = null;
        this.minhr = 1;
        this.maxhr = 12;
        this.minmin = 0;
        this.maxmin = 59;
        this.setfield = null;
        this.set24 = false;
        this.setafter = null;
    },
    spin: function(direction, segment) {
        if (direction==null) { if (this.timer!=null) {
          clearTimeout(this.timer);
          this.timer = null;
        }}
        else {
          let next = +this["h"+segment].innerHTML;
          next = direction ? next+1 : next-1;
          if (segment=="hr") {
            if (next > this.maxhr) { next = this.maxhr; }
            if (next < this.minhr) { next = this.minhr; }
          } else {
            if (next > this.maxmin) { next = this.maxmin; }
            if (next < this.minmin) { next = this.minmin; }
          }
          if (next<10) { next = "0"+next; }
          this["h"+segment].innerHTML = next;
          this.timer = setTimeout(() => { this.spin(direction, segment); }, 100);
        }
    },
    attach: function(instance) {
        instance.target.readOnly = true;
        instance.target.setAttribute("autocomplete", "off");
        if (instance["24"]==undefined) { instance["24"] = false; }
        this.show(instance);
    },
    show: function(instance){
        this.setfield = instance.target;
        this.setafter = instance.after;
        this.set24 = instance["24"];
        this.minhr = this.set24 ? 0 : 1 ;
        this.maxhr = this.set24 ? 23 : 12 ;
        let val = this.setfield.value;
        if (val=="") {
          this.hhr.innerHTML = instance.time.substring(0, 2);
          this.hmin.innerHTML = instance.time.substring(3, 5);
        } else {
          this.hhr.innerHTML = val.substring(0, 2);
          if (this.set24) {
            this.hmin.innerHTML = instance.time.substring(3, 5);
          } else {
            this.hmin.innerHTML = val.substring(3, 5);
          }
        }
        if (this.set24) { this.$el.addClass("tp-24"); }
        else { this.$el.removeClass("tp-24"); }
        this.$el.addClass("show");
    },
    set: function(e){
        if (this.set24) {
              this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML;
              if(this.setfield.id == 'time1'){
                this.parent.onChangeTime({target: this.setfield});
              } else {
                this.parent.onChangeTime2({target: this.setfield});
              }
            } else {
              this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML;
            }
            this.$el.removeClass("show");
            if (this.setafter) { this.setafter(this.setfield.value); }
    },
    setPosition:function(left, bottom){
        this.$el.find('#tp-box')[0].style.left = left;
        this.$el.find('#tp-box')[0].style.bottom = bottom;
    },
    close: function(e){
        this.$el.removeClass("show");
    }
});
    return TimePicker;

});
