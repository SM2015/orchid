$(document).ready(function () {
  $('[data-toggle=offcanvas]').click(function () {
    $('.row-offcanvas').toggleClass('active')
  });

$.ajax({
  dataType: "json",
  url: document.URL,
  success: function( data ) {
        $('#api').html(JSON.stringify(data, undefined, 2));
    }
});
});