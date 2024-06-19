odoo.define("odoo_website_helpdesk.ticket_details", function (require) {
  "use strict";

  $(document).on("mouseover", "#popover", function (event) {
    var self = this;
    var item_text = "";
    var element = $(this);
    if (self.parentElement.parentElement.children[3]) {
      item_text =
        "Ticket : " +
        self.parentElement.parentElement.children[1].outerText +
        "<br/>" +
        "Subject : " +
        self.parentElement.parentElement.children[2].outerText +
        "<br/>" +
        "Cost : " +
        self.parentElement.parentElement.children[4].outerText +
        "<br/>" +
        "Priority : " +
        self.parentElement.parentElement.children[6].outerText+
          "<br/>" +"<br/>" +
         "Description : " +
        self.parentElement.parentElement.children[3].outerText +
        "<br/>";
    }
    element.popover({
      html: true,
      placement: "right",
      trigger: "hover",
      title: "Ticket Details",
      content: "<span>" + item_text + "</span>",
    });
  });
});
