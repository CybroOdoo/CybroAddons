odoo.define('sale_product_image.tree_image', function (require) {
"use strict";
    
    
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;

       
    var ColumnBinaryImage = core.list_widget_registry.get('field').extend({
        /**
         * Return a link to the binary data as a Image
         */
        _format: function (row_data, options) {
                this.session = session;

                if (!row_data[this.id] || !row_data[this.id].value) {
                    return '';
                }
                var value = row_data[this.id].value, src;
                if (this.type === 'binary') {
                    if (value && value.substr(0, 10).indexOf(' ') === -1) {
                        // The media subtype (png) seems to be arbitrary
                        src = "data:image/png;base64," + value;
                    } else {
                        //src = instance.session.url('/web/binary/image', {model: options.model, field: this.id, id: options.id});
                        var imageArgs = {
                            model: options.model,
                            field: this.id,
                            id: options.id
                        }
                        if (this.resize) {
                            imageArgs.resize = this.resize;
                        }
                        src = session.url('/web/binary/image', imageArgs);
                    }
                } else {
                    if (!/\//.test(row_data[this.id].value)) {
                        src = '/web/static/src/img/icons/' + row_data[this.id].value + '.png';
                    } else {
                        src = row_data[this.id].value;
                    }
                }

                return QWeb.render('ListView.row.imagen', {widget: this, src: src});
            }
    });
    
    core.list_widget_registry
        .add('field.image', ColumnBinaryImage);
});
