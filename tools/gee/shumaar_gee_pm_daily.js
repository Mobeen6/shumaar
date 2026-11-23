// Shumaar: days of unhealthy air - daily PM2.5 by district, 2017-latest, for Google Earth Engine.
// Copernicus Atmosphere Monitoring Service (CAMS) near-real-time global analysis/forecast (ECMWF, ~40 km):
// surface PM2.5, averaged over each calendar day and each district. Shumaar then rescales each district's
// daily series to the ACAG/WashU satellite annual means (already on the site) and counts days above thresholds.
//
// 1. Paste into a NEW script and click Run. The Console prints the latest date available.
// 2. In Tasks, Run the export pak_pm_daily (about 3,500 days x 160 districts; allow a few hours).
//    Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('ECMWF/CAMS/NRT')
  .select('particulate_matter_d_less_than_25_um_surface');

var first = ee.Date('2017-01-01');
var last = ee.Date(Date.now()).advance(-1, 'day');   // up to yesterday (the collection also holds forecasts)
print('Up to:', last.format('YYYY-MM-dd'));
print('Check, Lahore-area mean for 1 Nov 2024 (should be ~100-300 ug/m3):', col.filterDate('2024-11-01','2024-11-02').mean().multiply(1e9)
  .reduceRegion({reducer: ee.Reducer.mean(), geometry: ee.Geometry.Point([74.33, 31.52]).buffer(20000), scale: 10000}));
var nDays = last.difference(first, 'day').floor();

var days = ee.List.sequence(0, nDays.subtract(1));
var out = ee.FeatureCollection(days.map(function(i) {
  var s = first.advance(ee.Number(i), 'day');
  var c = col.filterDate(s, s.advance(1, 'day'));
  var img = c.mean().multiply(1e9).rename('pm')                 // kg/m3 -> ug/m3
    .setDefaultProjection(col.first().projection());
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 10000, tileScale: 2})
    .map(function(f) {
      return ee.Feature(null, {d: s.format('YYYY-MM-dd'), id: f.get('id'), pm: f.get('mean'), n: c.size()});
    });
})).flatten();

Export.table.toDrive({
  collection: out, description: 'pak_pm_daily', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['d', 'id', 'pm', 'n']
});
