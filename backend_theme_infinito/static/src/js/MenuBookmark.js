/** @odoo-module alias=backend_theme_infinito.MenuBookmark **/
const { Component } = owl;
const { useState } = owl.hooks;
import session from 'web.session';

Component.prototype.dragElement = (elmnt, pos, display=true) => {
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    elmnt.onmousedown = dragMouseDown;
    function dragMouseDown(e) {
      elmnt.style.display = 'flex';
      e = e || window.event;
      e.preventDefault();
      pos3 = e.clientX;
      pos4 = e.clientY;
      document.onmouseup = closeDragElement;
      document.onmousemove = elementDrag;
    }
    function elementDrag(e) {
      e = e || window.event;
      e.preventDefault();
      pos1 = pos3 - e.clientX;
      pos2 = pos4 - e.clientY;
      pos3 = e.clientX;
      pos4 = e.clientY;
      if(pos.includes('y')){
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
      }
      if(pos.includes('x')){
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
      }
    }
    function closeDragElement() {
      document.onmouseup = null;
      document.onmousemove = null;
      if(!display){
        elmnt.style.display = 'none';
      }
    }
}

export default class MenuBookmark extends Component {
    constructor(parent){
        super();
        this.parent = parent;
    }
    willStart() {
        super.willStart();
        this.state = useState({
            menus: session.infinitoMenuBookmarks
        })
    }
    _mount() {
        this.mount(document.body);
    }
    _unmount() {
        this.unmount();
    }
    get menuBookmark() {
        return this.state.menus;
    }
    mounted(){
        super.mounted();
        this.dragElement(this.__owl__.refs.menuBookmark, 'y', false);
    }
}

MenuBookmark.template = 'backend_theme_infinito.MenuBookmark'