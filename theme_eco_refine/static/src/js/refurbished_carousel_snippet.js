odoo.define('theme_eco_refine.carousel_snippet', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    /**
     * Widget for Carousel snippets.
     */
    publicWidget.registry.refurb_carousel_snippet = publicWidget.Widget.extend({
         templates: 'theme_eco_refine.homepage_carousel',
         selector: '.main_body_refurbished_carousel',
         events:{
         },
         start: function() {
            var self = this;
            document.addEventListener('DOMContentLoaded', this.toggleDiv)
            self.$el[0].addEventListener('onload', ()=>{
                })
            return this._super.apply(this, arguments).then(async function () {
                await
                self.$el[0].addEventListener('onload', ()=>{
                })
                const carouselItems = self.el.querySelectorAll(".carousel-item");
                self.carouselItems = carouselItems
                self.startTypingForAll();
                const items = document.querySelectorAll('.ref-collection__item');
                items.forEach((item, index) => {
                    if (index === 0) {
                        item.classList.add('selected');
                    }
                    item.addEventListener('click', () => {
                        items.forEach(item => item.classList.remove('selected'));
                        item.classList.add('selected');
                    });
                });
            });
        },

        toggleDiv: function(ev)
        {
        ev.target.classList.add('active');
        },

        startTypingForAll:function() {
            var self = this;
            // Loop through each carousel item
            this.carouselItems.forEach(function (item) {
                // Get the text container element within the carousel item
                var textContainer = item.querySelector(".ref-hero__mainhead");
                // Get the text to type from the text container
                var textToType = textContainer.innerText;
                // Clear the text container
                textContainer.innerHTML = "";
                // Call the typeNextCharacter function initially for each text container
                self.typeNextCharacter(textContainer, textToType, 0);
            });
        },

        typeNextCharacter: function(textContainer, textToType, currentPosition) {
            var self = this;
             var typingDelay = 50;
             var repetitionDelay = 3000;
            // Get the next character from the text
            var nextCharacter = textToType.charAt(currentPosition);
            // Create a span element for the current character
            var span = document.createElement("span");
            // Determine the class to apply to the span element
            var spanClass = (currentPosition >= textToType.indexOf("Tech") && currentPosition < textToType.indexOf("Tech") + 4) ? "tech" : "";
            // Set the class of the span element
            span.className = spanClass;
           // Set the text content of the span element
           span.textContent = nextCharacter;
           // Append the span element to the text container
           textContainer.appendChild(span);
           // Increment the current position
            currentPosition++;
           // Check if there are more characters to type
           if (currentPosition < textToType.length) {
                // Schedule the next character typing
                setTimeout(function () {
                  self.typeNextCharacter(textContainer, textToType, currentPosition);
                }, typingDelay);
            } else {
                // When typing is complete, wait for the repetition delay and restart
                setTimeout(function () {
                  self.repeatTyping(textContainer, textToType);
                }, repetitionDelay);
            }
        },

        repeatTyping: function(textContainer, textToType) {
            var self = this;
            // Clear the text container
            textContainer.innerHTML = "";
            // Start the typing effect again for the current carousel item
            self.typeNextCharacter(textContainer, textToType, 0);
        },
    });
     return publicWidget.registry.refurb_carousel_snippet;
    });
