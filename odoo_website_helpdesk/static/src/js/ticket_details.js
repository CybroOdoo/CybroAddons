odoo.define("odoo_website_helpdesk.ticket_details", function (require) {
  "use strict";

  // Import the PublicWidget module
  var PublicWidget = require('web.public.widget');

  // Define the Template widget extend
  var Template = PublicWidget.Widget.extend({
    selector: ".o_portal_my_doc_table", //Select the table element
    events: {
        'mouseover #popover': '_onMouseover', // Register the mouseover event on the popover element
    },
    _onMouseover: function (event) {
      var item_text = "";
      // If the current target element has inner text
       if (event.currentTarget.innerText) {
      // Build the text to be displayed in the popover
      item_text =
        "Ticket : " +
        event.currentTarget.innerText +
        "<br/>" +
        "Subject : " +
        event.currentTarget.parentElement.parentElement.children[5].outerText+
        "<br/>" +
        "Cost : " +
        event.currentTarget.parentElement.parentElement.children[4].outerText +
        "<br/>" +
        "Priority : " +
        event.currentTarget.parentElement.parentElement.children[8].outerText+
          "<br/>" +"<br/>" +
         "Description : " +
        event.currentTarget.parentElement.parentElement.children[3].outerText +
        "<br/>";
    }
      // Initialize the popover with the built text
      $(event.currentTarget).popover({
        html: true,
        placement: "right",
        trigger: "hover",
        title: "Ticket Details",
        content: "<span>" + item_text + "</span>",
      });
    },
  });

  // Register the Template widget as 'ticket_form'
  PublicWidget.registry.ticket_form = Template;
  return Template;
});
