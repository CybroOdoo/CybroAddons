/** @odoo-module */
import BasicFields from 'web.basic_fields';
var FieldBinaryImage = BasicFields.FieldBinaryImage;
var core = require('web.core');
var qweb = core.qweb;
var utils = require('web.utils');

FieldBinaryImage.include({
    _render: function () {
        var self = this;
        var url = this.placeholder;
        if (this.recordData.file_name && this.recordData.file_name.endsWith('.pdf')){
            url = `/ocr_data_retrieval/static/src/img/pdf.png`
        }
        if (this.value) {
            if (!utils.is_bin_size(this.value)) {
                // Use magic-word technique for detecting image type
                url = 'data:image/' + (this.file_type_magic_word[this.value[0]] || 'png') + ';base64,' + this.value;
            } else {
                var field = this.nodeOptions.preview_image || this.name;
                var unique = this.recordData.__last_update;
                url = this._getImageUrl(this.model, this.res_id, field, unique);
            }
        }
        var $img = $(qweb.render("FieldBinaryImage-img", {widget: this, url: url}));
        // override css size attributes (could have been defined in css files)
        // if specified on the widget
        var width = this.nodeOptions.size ? this.nodeOptions.size[0] : this.attrs.width;
        var height = this.nodeOptions.size ? this.nodeOptions.size[1] : this.attrs.height;
        if (width) {
            $img.attr('width', width);
            $img.css('max-width', width + 'px');
            if (!height) {
                $img.css('height', 'auto');
                $img.css('max-height', '100%');
            }
        }
        if (height) {
            $img.attr('height', height);
            $img.css('max-height', height + 'px');
            if (!width) {
                $img.css('width', 'auto');
                $img.css('max-width', '100%');
            }
        }
        this.$('> img').remove();
        this.$el.prepend($img);
        $img.one('error', function () {
            $img.attr('src', self.placeholder);
            self.displayNotification({ message: _t("Could not display the selected image"), type: 'danger' });
        });
    },
});
