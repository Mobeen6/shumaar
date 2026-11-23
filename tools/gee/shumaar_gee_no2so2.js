// Shumaar: NO2 (traffic, industry) and SO2 (coal, oil) by district, monthly from mid-2018, for Google Earth Engine.
// Copernicus Sentinel-5P TROPOMI offline level-3 products, monthly mean of daily images, district mean at 5 km.
//
// 1. Paste into a NEW script and click Run.
// 2. In Tasks, Run the export pak_no2_so2_monthly (allow an hour or two). Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var no2 = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2').select('tropospheric_NO2_column_number_density');
var so2 = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_SO2').select('SO2_column_number_density');

var first = ee.Date('2018-08-01');
var last = ee.Date(no2.aggregate_max('system:time_start'));
var nMonths = last.difference(first, 'month').floor();
print('Months:', nMonths);

var out = ee.FeatureCollection(ee.List.sequence(0, nMonths.subtract(1)).map(function(i) {
  var s = first.advance(ee.Number(i), 'month'), e = s.advance(1, 'month');
  var img = ee.Image.cat([
    no2.filterDate(s, e).mean().multiply(1e6).rename('no2'),   // umol/m2
    so2.filterDate(s, e).mean().multiply(1e6).rename('so2')
  ]).setDefaultProjection(ee.Projection('EPSG:4326').atScale(1113.2));
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 5000, tileScale: 2})
    .map(function(f) { return ee.Feature(null, {m: s.format('YYYY-MM'), id: f.get('id'), no2: f.get('no2'), so2: f.get('so2')}); });
})).flatten();

Export.table.toDrive({collection: out, description: 'pak_no2_so2_monthly', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['m', 'id', 'no2', 'so2']});
