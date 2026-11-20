// Shumaar: warming stripes - monthly day and night temperatures by district, 1981-latest, for Google Earth Engine.
// ECMWF ERA5-Land daily aggregates (reanalysis, ~11 km): mean of daily minimum (nights) and daily maximum (days)
// for every calendar month, averaged over each district.
//
// 1. Paste into a NEW script and click Run. The Console prints the latest day available.
// 2. In Tasks, Run the export pak_temp_monthly (about 540 months x 160 districts; allow an hour or two).
//    Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR').select(['temperature_2m_min', 'temperature_2m_max']);

var first = ee.Date('1981-01-01');
var last = ee.Date(col.aggregate_max('system:time_start'));
print('Latest day:', last.format('YYYY-MM-dd'));
var nMonths = last.difference(first, 'month').floor();      // complete months only

var months = ee.List.sequence(0, nMonths.subtract(1));
var out = ee.FeatureCollection(months.map(function(i) {
  var s = first.advance(ee.Number(i), 'month');
  var c = col.filterDate(s, s.advance(1, 'month'));
  var img = c.mean().subtract(273.15).rename(['tmin', 'tmax'])
    .setDefaultProjection(col.first().projection());
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 11132, tileScale: 2})
    .map(function(f) {
      return ee.Feature(null, {m: s.format('YYYY-MM'), id: f.get('id'), tmin: f.get('tmin'), tmax: f.get('tmax'), days: c.size()});
    });
})).flatten();

Export.table.toDrive({
  collection: out, description: 'pak_temp_monthly', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['m', 'id', 'tmin', 'tmax', 'days']
});
