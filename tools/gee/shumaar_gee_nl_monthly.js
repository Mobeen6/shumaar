// Shumaar: monthly night lights by district, 2012-present, for Google Earth Engine.
// Built from NASA Black Marble daily nights (VNP46A2, the same source as the annual night-light layers):
// for each calendar month, the median of all cloud-free nights, averaged over each district at 1 km.
// Used to spot dimming episodes (load-shedding, outages) and set them against NEPRA generation data.
//
// 1. Paste into a NEW script and click Run. The Console prints the latest night and the number of months.
// 2. In Tasks, Run the export pak_nl_monthly. It is one long table (about 170 months x 160 districts);
//    allow an hour or two. Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('NASA/VIIRS/002/VNP46A2')
  .select('Gap_Filled_DNB_BRDF_Corrected_NTL');

var first = ee.Date('2012-02-01');
var last = ee.Date(col.aggregate_max('system:time_start'));
var nMonths = last.difference(first, 'month').floor();
print('Latest night:', last.format('YYYY-MM-dd'), 'Months:', nMonths);

var months = ee.List.sequence(0, nMonths.subtract(1));
var out = ee.FeatureCollection(months.map(function(i) {
  var s = first.advance(ee.Number(i), 'month');
  var c = col.filterDate(s, s.advance(1, 'month'));
  var img = c.median().setDefaultProjection(col.first().projection());
  var m = s.format('YYYY-MM');
  var nights = c.size();
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 1000, tileScale: 2})
    .map(function(f) {
      return ee.Feature(null, {m: m, id: f.get('id'), n: f.get('n'), mean_nw: f.get('mean'), nights: nights});
    });
})).flatten();

Export.table.toDrive({
  collection: out, description: 'pak_nl_monthly', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['m', 'id', 'n', 'mean_nw', 'nights']
});
