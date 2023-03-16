/** @odoo-module **/


import { patch } from "@web/core/utils/patch";
import { Dialog } from "@web/core/dialog/dialog";

const { Component, useExternalListener, onMounted } = owl;
//This code defines a function called "draggable" that enables a DOM element to be
// dragged around the screen by clicking and dragging it. This function is called
// in the "mount" method of a Dialog object, which is part of the Owl web framework.

//Parameters:
//- el (object): The event object that triggered the function. This is used to get the target element that should be draggable.

patch(Dialog.prototype,'/dragable_and_resizable_wizard/static/src/js/draggable_wiz.js',{
    /**
     * Modifies the `Dialog` prototype's `setup` method to include the `mount` method.
     */
    setup() {
        this._super.apply();
        onMounted(this.mount)
    },

    /**
     * Attaches a `click` event listener to the dialog element to enable dragging.
     */
    mount(){
        this.__owl__.bdom.children[0].parentEl.addEventListener('click', this.draggable)
    },

    /**
     * Attaches event listeners to the dialog element for `mousedown`, `mousemove`, and `mouseup` events,
     * enabling the user to drag the element around the screen.
     * @param {MouseEvent} el - The `mousedown` event.
     */
    draggable(el) {

          el.target.addEventListener('mousedown', function(e) {
            var offsetX = e.clientX - parseInt(window.getComputedStyle(this).left);
            var offsetY = e.clientY - parseInt(window.getComputedStyle(this).top);

            function mouseMoveHandler(e) {
              el.target.style.top = (e.clientY - offsetY) + 'px';
              el.target.style.left = (e.clientX - offsetX) + 'px';
            }

            function reset() {
              window.removeEventListener('mousemove', mouseMoveHandler);
              window.removeEventListener('mouseup', reset);
            }

            window.addEventListener('mousemove', mouseMoveHandler);
            window.addEventListener('mouseup', reset);
        });
    },
});
//Once you have created the dialog and added the draggable function, you can use
//the dialog in your application and the user will be able to drag it around
//the screen by clicking and dragging the dialog's title bar.
