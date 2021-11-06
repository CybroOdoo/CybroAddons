odoo.define('bom_components_image.binary_image', function (require) {
"use strict";
    
    
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;

       
    var AllBinaryImage = core.list_widget_registry.get('field').extend({

        _format: function (row_image, options) {
                this.session = session;

                if (!row_image[this.id] || !row_image[this.id].value) {
                    return '';
                }
                var value = row_image[this.id].value, src;
                if (this.type === 'binary') {
                    if (value && value.substr(0, 10).indexOf(' ') === -1) {
                        src = "data:image/png;base64," + value;
                    } else {
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
                    if (!/\//.test(row_image[this.id].value)) {
                        src = '/web/static/src/img/icons/' + row_image[this.id].value + '.png';
                    } else {
                        src = row_image[this.id].value;
                    }
                }

                return QWeb.render('ListView.row.imagen', {widget: this, src: src});
            }
    });
    
    core.list_widget_registry
        .add('field.image', AllBinaryImage);
});
