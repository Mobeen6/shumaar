// Shumaar: monthly night lights by district, 2012-present (NASA Black Marble VNP46A3 monthly composites).
// For load-shedding / outage analysis: monthly mean radiance per district, one long table.
//
// 1. Paste into a NEW script and click Run. The Console prints how many monthly images there are (~170).
// 2. In Tasks, Run the export pak_nl_monthly.csv. It is one long table (months x 160 districts); allow an hour or two.
// 3. Send the CSV back.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('NASA/VIIRS/002/VNP46A3').select('Gap_Filled_DNB_BRDF_Corrected_NTL');
print('Monthly images:', col.size(), 'latest:',
  ee.Date(col.aggregate_max('system:time_start')).format('YYYY-MM'));

var out = col.map(function(img) {
  var m = ee.Date(img.get('system:time_start')).format('YYYY-MM');
  return img.reduceRegions({
    collection: districts, reducer: ee.Reducer.mean(), scale: 1000, tileScale: 2
  }).map(function(f) {
    return ee.Feature(null, {m: m, id: f.get('id'), n: f.get('n'), mean_nw: f.get('mean')});
  });
}).flatten();

Export.table.toDrive({
  collection: out, description: 'pak_nl_monthly', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['m', 'id', 'n', 'mean_nw']
});
