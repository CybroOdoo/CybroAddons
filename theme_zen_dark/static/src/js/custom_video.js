$(document).ready(function () {
      var url = $("#Geeks3").attr('src');
      $("#Geeks2").on('hide.bs.modal', function () {
        $("#Geeks3").attr('src', '');
      });
      $("#Geeks2").on('show.bs.modal', function () {
        $("#Geeks3").attr('src', url);
      });
    }); 