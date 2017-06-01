(function ($) {
    $(document).ready(function() {
        $('.xzoom, .xzoom-gallery').xzoom({
            zoomWidth: '250',
            zoomHeight: '250',
            title: false,
            tint: '#333',
            Xoffset: 15,
            scroll: true,
            fadeTrans: true,
            position: 'lens',
            lensShape: 'square',
            sourceClass: 'xzoom-hidden',
            hover: true,
        });
});})(jQuery);