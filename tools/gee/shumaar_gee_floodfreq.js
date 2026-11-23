// Shumaar: how often each district floods, 2000-2018, for Google Earth Engine.
// Global Flood Database (Tellman et al. 2021, Nature): 913 large floods mapped from MODIS at 250 m.
// For each district: share of land flooded at least once, and land flooded 3+ times; plus a per-event table.
//
// 1. Paste into a NEW script and click Run. The Console prints how many events touch Pakistan.
// 2. In Tasks, Run both exports: pak_flood_freq and pak_flood_events. Send back both CSVs.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var pak = districts.geometry().bounds();
var gfd = ee.ImageCollection('GLOBAL_FLOOD_DB/MODIS_EVENTS/V1').filterBounds(pak);
print('Flood events touching Pakistan:', gfd.size());

// flooded water excluding permanent water (jrc_perm_water band)
var flooded = gfd.map(function(i) { return i.select('flooded').and(i.select('jrc_perm_water').not()).unmask(0); });
var times = flooded.sum().rename('times');
var area = ee.Image.pixelArea().divide(1e6);
var stats = ee.Image.cat([
  area.rename('area_km2'),
  area.updateMask(times.gte(1)).rename('flood1_km2'),
  area.updateMask(times.gte(3)).rename('flood3_km2')
]).reduceRegions({collection: districts, reducer: ee.Reducer.sum(), scale: 250, tileScale: 4})
  .map(function(f) { return f.setGeometry(null); });
Export.table.toDrive({collection: stats, description: 'pak_flood_freq', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['id', 'n', 'p', 'area_km2', 'flood1_km2', 'flood3_km2']});

// per event: flooded km2 in each district (only rows with any flooding are kept)
var ev = ee.FeatureCollection(gfd.toList(200).map(function(i) {
  i = ee.Image(i);
  var f = i.select('flooded').and(i.select('jrc_perm_water').not()).selfMask();
  return area.updateMask(f).rename('km2').reduceRegions({collection: districts, reducer: ee.Reducer.sum(), scale: 250, tileScale: 4})
    .filter(ee.Filter.gt('sum', 0))
    .map(function(d) { return ee.Feature(null, {id: d.get('id'), km2: d.get('sum'),
      event: i.get('id'), began: ee.Date(i.get('began')).format('YYYY-MM-dd'), cause: i.get('dfo_main_cause')}); });
})).flatten();
Export.table.toDrive({collection: ev, description: 'pak_flood_events', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['event', 'began', 'cause', 'id', 'km2']});
