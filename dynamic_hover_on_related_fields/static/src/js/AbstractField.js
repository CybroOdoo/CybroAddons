odoo.define("dynamic_hover_on_related_fields.web", function (require) {
  "use strict";

  var AbstractField = require("web.AbstractField");
  var session = require("web.session");
  var rpc = require("web.rpc");
  var core = require('web.core');
  var QWeb = core.qweb;

  AbstractField.include({
    events: _.extend({}, AbstractField.prototype.events, {
        'mousemove': '_onMouseMove',
    }),
    init: function () {
      this._super.apply(this, arguments);
    },
    async getDataFromBackend() {
        const str_info = {
            resModel: this.model,
            resId: this.res_id,
            debug: Boolean(odoo.debug),
            field: {
                name: this.field.name,
                type: this.field.type,
                widget: this.attrs.widget,
                relation: this.field.relation,
                formatType: this.formatType,
                m2o_value: this.m2o_value,
            },
        }
        const info = JSON.stringify(str_info)
        if(this?.res_id){
            const requiredData = await rpc.query({
                model: "hover.related.fields",
                method: "finding_the_data_to_show_tooltip",
                args: [info]
            });
            this.requiredData = requiredData;
        }
    },

    _onMouseMove: async function (ev) {
        await this.getDataFromBackend();
        const data = this.requiredData
        if (Array.isArray(data) && data.length > 0)
        {
            this.$el.tooltip({
                delay: { show: 500, hide: 100 },
                title: function () {
                    return QWeb.render('hover_template', {
                        requiredData: data[0],
                    });
                }
           });
        }
    },
  });
});