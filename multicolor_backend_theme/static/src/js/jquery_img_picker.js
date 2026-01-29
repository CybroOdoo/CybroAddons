(function ($) {
    $.fn.imagePicker = function (options) {

        // Define plugin options
        var settings = $.extend({
            // Input name attribute
            name: "",

            // Classes for styling the input
            class: "form-control btn btn-default btn-block",
            // Icon which displays in center of input
            icon: "fa fa-plus"
        }, options);

        // Create an input inside each matched element
        return this.each(function () {
            $(this).html(create_btn(this, settings));
        });

    };

    // Private function for creating the input element
    function create_btn(that, settings) {
        // The input icon element
        var picker_btn_icon = $('<i class="' + settings.icon + '"></i>');
///home/cybrosys/odoo14
        if (settings.remove != true && settings.widget.active_theme.sidebar_image) {
            var picker_btn_input = create_preview(
                that,
                settings.widget.active_theme.sidebar_image,
                settings);
            var picker_btn = picker_btn_input;
        }
        else {
            // The actual file input which stays hidden
            var picker_btn_input = $('<input type="file" name="' + settings.name + '" />');
            var picker_btn = $('<div class="' + settings.class + ' img-upload-btn"></div>')
                .append(picker_btn_icon)
                .append(picker_btn_input);
        }
        // The actual element displayed


        // File load listener
        picker_btn_input.change(function () {
            if ($(this).prop('files')[0]) {
                // Use FileReader to get file
                var reader = new FileReader();

                // Create a preview once image has loaded
                reader.onload = function (e) {
                    var preview = create_preview(that, e.target.result, settings);
                    $(that).html(preview);
                    settings.widget._onImageLoad(e.target.result);
                };

                // Load image
                reader.readAsDataURL(picker_btn_input.prop('files')[0]);
            }
        });

        return picker_btn
    };

    // Private function for creating a preview element
    function create_preview(that, src, settings) {

        // The preview image
        var picker_preview_image = $('<img src="' + src + '" class="img-responsive img-rounded" />');

        // The remove image button
        var picker_preview_remove = $('<button class="btn btn-link fa fa-trash-o"><small></small></button>');

        // The preview element
        var picker_preview = $('<div class="image-container"></div>')
            .append(picker_preview_image)
            .append(picker_preview_remove);

        // Remove image listener
        picker_preview_remove.click(function () {
            settings.remove = true;
            var btn = create_btn(that, settings);
            $(that).html(btn);
            settings.widget._onRemoveImage();
        });

        return picker_preview;
    };

}(jQuery));

$(document).ready(function () {
    $('.img-picker').imagePicker({name: 'images'});
});
