// Shumaar: extreme heat days by district, 1981-latest, for Google Earth Engine.
// ECMWF ERA5-Land daily aggregates (~11 km), the same source as the warming stripes.
// For each year and district: average number of days with a daily maximum above 40 C and 45 C,
// and of nights whose minimum stayed above 30 C (no relief overnight).
//
// 1. Paste into a NEW script and click Run.
// 2. In Tasks, Run the export pak_heat_days (a few minutes to an hour). Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').select(['temperature_2m_max', 'temperature_2m_min']);
var lastYear = ee.Date(col.aggregate_max('system:time_start')).get('year');
print('Latest year with data:', lastYear);

var years = ee.List.sequence(1981, lastYear);
var out = ee.FeatureCollection(years.map(function(y) {
  var s = ee.Date.fromYMD(y, 1, 1), c = col.filterDate(s, s.advance(1, 'year'));
  var img = ee.Image.cat([
    c.map(function(i) { return i.select('temperature_2m_max').gt(313.15); }).sum().rename('d40'),
    c.map(function(i) { return i.select('temperature_2m_max').gt(318.15); }).sum().rename('d45'),
    c.map(function(i) { return i.select('temperature_2m_min').gt(303.15); }).sum().rename('n30')
  ]).setDefaultProjection(col.first().projection());
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 11132, tileScale: 2})
    .map(function(f) { return f.setGeometry(null).set({year: y, days: c.size()}); });
})).flatten();

Export.table.toDrive({collection: out, description: 'pak_heat_days', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['id', 'n', 'year', 'days', 'd40', 'd45', 'n30']});
