$(document).ready(function () {
  $('[data-toggle=offcanvas]').click(function () {
    $('.row-offcanvas').toggleClass('active')
  });

$( "#api-accordion" ).click(function() {
  $.ajax({
  dataType: "json",
  url: document.URL,
  success: function( data ) {
        $('#api').html(JSON.stringify(data, undefined, 2));
        $('pre code').each(function(i, e) {
            console.log(e);
            hljs.highlightBlock(e)
        });
    }
});
});


});