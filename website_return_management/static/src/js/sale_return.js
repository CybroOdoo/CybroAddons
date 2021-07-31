odoo.define('website_return_management.return', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    $("#hidden_box_btn").on('click', function () {
        $('#hidden_box').modal('show');

    })

    $("#product").on('change', function(){

    var x = $('#submit');
    x.addClass('d-none');
    if ($("#product").val()=='none')
    {
        if (!x.hasClass('d-none'))
            {
            x.addClass('d-none');
            }
    }
    else
    {
        if (x.hasClass('d-none'))
        {
            x.removeClass('d-none');
        }
    }
    })


});