odoo.define('dragable_and_resizable_wizard.draggable_wiz.js', function (require) {
'use strict';
const Dialog = require('web.Dialog');
//This code defines a function called "draggable" that enables a DOM element to be
// dragged around the screen by clicking and dragging it.
//Parameters:
//- el (object): The event object that triggered the function. This is used to get the target element that should be draggable.
    Dialog.include({
        /**
         * Modifies the `Dialog` `start` method to include the `drag` function.
         */
          async start() {
                await this._super(...arguments);
                this.drag()
          },
          /**
           * Attaches a `click` event listener to the dialog element to enable dragging.
           */
          drag(){
            this.$modal[0].firstElementChild.children[0].addEventListener('click', this.draggable)
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
                        return
                    }
                    if (e.target.className === "modal-header"){
                        window.addEventListener('mousemove', mouseMoveHandler);
                        window.addEventListener('mouseup', reset);
                    }
                });
          },
    });
});
//Once you have created the dialog and added the draggable function, you can use
//the dialog in your application and the user will be able to drag it around
//the screen by clicking and dragging the dialog's title bar.
