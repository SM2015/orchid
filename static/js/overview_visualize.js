//for each meta_series
//grab the percent passing and add it to the top
//add each other series to its graph

orchid_vis = {
    locations:[],
    location_cursor:null,
    month:["January","February","March","April","May","June","July","August","September","October","November","December"],
    get_chart_by_id:function(id){
        var index=$("#container-"+String(id)).data('highchartsChart');
        return Highcharts.charts[index];
    },
apply_chart:function(dom_object, series_data_blob, chart_title, legend_enabled) {

    return    dom_object.highcharts({
        chart: {
            type: 'spline'
        },
        title: {
            text: chart_title
        },
        subtitle: {
            text: 'Click legend to select lines.'
        },
        xAxis: {
            type: 'datetime',
            tickInterval: 30 * 24 * 3600 * 1000,
            dateTimeLabelFormats: { // don't display the dummy year
            month: '%e. %b',
            year: '%b'
        },
        title: {
            text: 'Date'
        }
    },
    yAxis: {
        title: {
            text: 'Score (%)'
        },
        min: 0,
        max:100
    },
    legend: {
        enabled: legend_enabled
    },
    tooltip: {
        headerFormat: '<b>{series.name}</b><br>',
        pointFormat: '{point.x: %b %Y}: {point.y:.2f}%'
    },
    series: series_data_blob
});

},
    load_next_location:function(){
        if(orchid_vis.location_cursor==null){
            orchid_vis.location_cursor = orchid_vis.location_cursor=0;
        }
        else{
            //update the cursor
            orchid_vis.location_cursor = orchid_vis.location_cursor+1;
        }
        next_location_id = orchid_vis.locations[orchid_vis.location_cursor].id;
        //load the location's json
        $.getJSON( "location/"+String(next_location_id)+"/visualize", function( data ) {
          for(var q in data.series){
            s = data.series[q];
            console.log(s);
            if(s.id != undefined){
            var loading_chart = orchid_vis.get_chart_by_id(s.id);
            loading_chart.addSeries({
            name: data.noun.title,
            data: s.data
            });
        }
          }
          $('#loaded_counter').html(String(orchid_vis.location_cursor)+"/"+String(orchid_vis.locations.length)+" Loaded");
          orchid_vis.load_next_location();
          });
         
    }
}


orchid_vis.apply_chart($('#container-p'), [], "Percent Of Goals Met", true);
var index=$("#container-p").data('highchartsChart');
var mychart=Highcharts.charts[index];

mychart.setTitle("hello!");

$( ".indicator-chart" ).each(function( index ) {
  orchid_vis.apply_chart($(this), [], $(this).data( "indicator-title" ), true);
});

$.getJSON( "location/list/plain", function( data ) {
  $.each( data.locations, function( key, val ) {
    orchid_vis.locations.push(val);
  });

  $('#loaded_counter').html("0/"+String(orchid_vis.locations.length)+" Loaded");
  orchid_vis.load_next_location();
 

});
