/** @odoo-module **/
import core from 'web.core';
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var qweb = core.qweb

//Extended the widget to create custom systray widget
const SystrayWidget = Widget.extend({
  template: 'pdf_report_action.IconSystrayDropdown',
  events: {
      'click .o-dropdown': '_onClick',
  },
  _onClick: function(ev){ //  Function on clicking the systray icon
       this.do_action({
      type: 'ir.actions.act_window',
      name: 'Report Action',
      res_model: 'dynamic.action',
      views: [[false, 'form']],
       target: 'new',
    });
  },
});
SystrayMenu.Items.push(SystrayWidget);
export default SystrayWidget;
