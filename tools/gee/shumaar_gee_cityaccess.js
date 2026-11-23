// Shumaar: travel time to the nearest city, by district, for Google Earth Engine.
// Malaria Atlas Project "accessibility to cities 2015" (Weiss et al. 2018, Nature): minutes to the nearest
// urban centre of 50,000+ people by the fastest mode (roads, rail, water, walking), at about 1 km.
// Weighted by WorldPop 2020 population, the same population layer as the health-access layer.
//
// 1. Paste into a NEW script and click Run.
// 2. In Tasks, Run the export pak_city_access (a few minutes). Send back the CSV.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var acc = ee.Image('Oxford/MAP/accessibility_to_cities_2015_v1_0').select('accessibility');
var pop = ee.ImageCollection('WorldPop/GP/100m/pop').filter(ee.Filter.eq('country', 'PAK'))
  .filter(ee.Filter.eq('year', 2020)).first();

// put population on the accessibility grid (sum of 100 m people in each ~1 km cell)
var popC = pop.reduceResolution({reducer: ee.Reducer.sum().unweighted(), maxPixels: 1024})
  .reproject(acc.projection()).rename('pop');
var img = ee.Image.cat([
  popC,
  popC.multiply(acc).rename('popmin'),
  popC.updateMask(acc.gt(60)).rename('pop60'),
  popC.updateMask(acc.gt(120)).rename('pop120'),
  popC.updateMask(acc.gt(180)).rename('pop180')
]);
var out = img.reduceRegions({collection: districts, reducer: ee.Reducer.sum(), crs: acc.projection(), tileScale: 4})
  .map(function(f) { return f.setGeometry(null); });

Export.table.toDrive({collection: out, description: 'pak_city_access', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['id', 'n', 'p', 'pop', 'popmin', 'pop60', 'pop120', 'pop180']});
