function initialize() {
    console.log("hello world");
  var markers = [];
  var myLatlng = new google.maps.LatLng(-25.363882,131.044922);
  var mapOptions = {
    zoom: 4,
    center: myLatlng
  }
  var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

$.getJSON( "location/list", function( data ) {
  var items = [];
  $.each( data, function( key, val ) {
    console.log(val);

      var marker = new google.maps.Marker({
          position: new google.maps.LatLng(val.lattitude,val.longitude),
          map: map,
          title: val.title
      });
      markers.push(marker);

  });
});

}

google.maps.event.addDomListener(window, 'load', initialize);