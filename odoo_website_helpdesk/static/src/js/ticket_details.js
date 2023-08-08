odoo.define("odoo_website_helpdesk.ticket_details", function (require) {
  "use strict";
  var PublicWidget = require('web.public.widget');
  var Template = PublicWidget.Widget.extend({
    selector: ".o_portal_my_doc_table",
    events: {
        'mouseover #popover': '_onMouseover',
    },
//    Show the details as hover when cursor is moves over the ticket
    _onMouseover: function (event) {
      var item_text = "";
       if (event.currentTarget.innerText) {
      item_text =
        "Ticket : " +
        event.currentTarget.innerText +
        "<br/>" +
        "Subject : " +
        event.currentTarget.parentElement.parentElement.children[2].outerText+
        "<br/>" +
        "Cost : " +
        event.currentTarget.parentElement.parentElement.children[4].outerText +
        "<br/>" +
        "Priority : " +
        event.currentTarget.parentElement.parentElement.children[5].outerText+
          "<br/>" +
         "Description : " +
        event.currentTarget.parentElement.parentElement.children[3].outerText +
        "<br/>";
    }
      $(event.currentTarget).popover({
        html: true,
        placement: "right",
        trigger: "hover",
        title: "Ticket Details",
        content: "<span>" + item_text + "</span>",
      });
    },
  });
  PublicWidget.registry.ticket_form = Template;
  return Template;
});