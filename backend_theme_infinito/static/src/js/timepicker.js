/** @odoo-module alias=backend_theme_infinito.timepicker **/
const { Component } = owl;
const { xml } = owl.tags;
const { useRef } = owl.hooks;


export default class TimePicker extends Component {
    constructor(parent){
        super();
        this.parent = parent;
    }
    setup(){
        super.setup();
        this.hhr = null;
        this.hmin = null;
        this.hap = null;
    }
    mounted(){
        super.mounted();
        this.hwrap = useRef('timePicker').el;
        for (let segment of ["hr", "min", "ap"]) {
            let up = this.hwrap.querySelector(`#tp-${segment} .tp-up`),
            down = this.hwrap.querySelector(`#tp-${segment} .tp-down`);
            this["h"+segment] = this.hwrap.querySelector(`#tp-${segment} .tp-val`);
      
            if (segment=="ap") {
              up.onclick = () => { this.spin(true, segment); };
              down.onclick = () => { this.spin(true, segment); };
            } else {
              up.onmousedown = () => { this.spin(true, segment); };
              down.onmousedown = () => { this.spin(false, segment); };
              up.onmouseup = () => { this.spin(null); };
              down.onmouseup = () => { this.spin(null); };
              up.onmouseleave = () => { this.spin(null); };
              down.onmouseleave = () => { this.spin(null); };
            }
        }
        this.timer = null;
        this.minhr = 1;
        this.maxhr = 12;
        this.minmin = 0;
        this.maxmin = 59;
        this.setfield = null;
        this.set24 = false;
        this.setafter = null;
    }
    _mount(){
        this.mount(document.body);
    }
    spin(direction, segment) {
        if (direction==null) { if (this.timer!=null) {
          clearTimeout(this.timer);
          this.timer = null;
        }}
        else if (segment=="ap") { this.hap.innerHTML = this.hap.innerHTML=="AM" ? "PM" : "AM"; }
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
    }
    attach(instance) {
        instance.target.readOnly = true;
        instance.target.setAttribute("autocomplete", "off");
        if (instance["24"]==undefined) { instance["24"] = false; }
        this.show(instance);
    }
    show(instance){
        this.setfield = instance.target;
        this.setafter = instance.after;
        this.set24 = instance["24"];
        this.minhr = this.set24 ? 0 : 1 ;
        this.maxhr = this.set24 ? 23 : 12 ;
        let val = this.setfield.value;
        if (val=="") {
          this.hhr.innerHTML = instance.time.substring(0, 2);
          this.hmin.innerHTML = instance.time.substring(3, 5);
          this.hap.innerHTML = "AM";
        } else {
          this.hhr.innerHTML = val.substring(0, 2);
          if (this.set24) {
            this.hmin.innerHTML = instance.time.substring(3, 5);
          } else {
            this.hmin.innerHTML = val.substring(3, 5);
          }
        }
        if (this.set24) { this.hwrap.classList.add("tp-24"); }
        else { this.hwrap.classList.remove("tp-24"); }
        this.hwrap.classList.add("show");
    }
    set(){
        if (this.set24) {
          this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML;
          if(this.setfield.id == 'time1'){
            this.parent.onChangeTime({target: this.setfield});
          } else {
            this.parent.onChangeTime2({target: this.setfield});
          }
        } else {
          this.setfield.value = this.hhr.innerHTML + ":" + this.hmin.innerHTML + " " + this.hap.innerHTML;
        }
        this.hwrap.classList.remove("show");
        if (this.setafter) { this.setafter(this.setfield.value); }
    } 
    setPosition(left, bottom){
        this.hwrap.querySelector('#tp-box').style.left = left;
        this.hwrap.querySelector('#tp-box').style.bottom = bottom;
    }
    close(){
        this.hwrap.classList.remove("show");
    }
}

TimePicker.template = xml`<div t-ref="timePicker" id="tp-wrap"><div id="tp-box">
<div class="tp-cell" id="tp-hr">
  <div class="tp-up">&#65087;</div> <div class="tp-val">0</div> <div class="tp-down">&#65088;</div>
</div>
<div class="tp-cell" id="tp-min">
  <div class="tp-up">&#65087;</div> <div class="tp-val">0</div> <div class="tp-down">&#65088;</div>
</div>
<div class="tp-cell" id="tp-ap">
  <div class="tp-up">&#65087;</div> <div class="tp-val">AM</div> <div class="tp-down">&#65088;</div>
</div>
<button id="tp-close" t-on-click="close">Close</button>
<button id="tp-set" t-on-click="set">Set</button>
</div></div>`;