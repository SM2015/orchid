//set up the map
function initMap()
{
  var myOptions = {
    mapTypeId: google.maps.MapTypeId.ROADMAP
};
map = new google.maps.Map(document.getElementById('map-canvas'), myOptions);
}

//set up your markers
function initMarkers()
{
    $.getJSON( "location/list", function( data ) {
      var items = [];
      $.each( data['locations'], function( key, val ) {
        console.log("val");
        console.log(val);

        var marker = new google.maps.Marker({
          position: new google.maps.LatLng(val.lattitude,val.longitude),
          map: map,
          title: val.title
      });
        google.maps.event.addListener(marker, 'click', function() {
        map.setCenter(marker.getPosition());
        window.location = val.id;
        });

        markers.push(marker);

    });
      //set map to show all markers
      for(var i in markers)
      {
        bound.extend(markers[i].getPosition());
    }
    map.fitBounds(bound);
    console.log(map.getZoom());
    map.setZoom(15);
});

}

var map;
var bound = new google.maps.LatLngBounds();
var markers = new Array();

//jQuery style entry point, change if necessary
$(document).ready(function(){
  initMap();
  initMarkers();
});