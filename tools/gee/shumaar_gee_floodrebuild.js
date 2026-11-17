// Shumaar: building back in the 2022 flood zone, for Google Earth Engine.
// How much construction since 2022 sits on land that was under water in Aug-Sep 2022.
//
// 1. Paste into a NEW script and click Run. The Console prints the flood area as a check (~ tens of thousands of km2).
// 2. In Tasks, Run both exports: pak_flood_rebuild.csv (district table) and flood_rebuild_sindh.tif (map of the worst belt).
// 3. Send both files back.
//
// Data
//   Flood water: Dynamic World V1 (Sentinel-2, 10 m) water class, 15 Aug - 30 Sep 2022,
//     minus permanent water (JRC Global Surface Water occurrence > 50%).
//   New construction: Esri-Impact Observatory 10 m land cover, built area in the latest year but not in 2022.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var pak = districts.geometry().bounds().buffer(10000);

// ---- flood extent, Aug-Sep 2022 ----
var dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
  .filterDate('2022-08-15', '2022-10-01').filterBounds(pak).select('label');
var water22 = dw.map(function(i) { return i.eq(0); }).max();          // water at any time in the window
var perm = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence').gte(50).unmask(0);
var flood = water22.and(perm.not());

// ---- built-up change since 2022 ----
var esri = ee.ImageCollection('projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS');
var lastYear = ee.Date(esri.aggregate_max('system:time_start')).get('year');
print('Latest Esri land-cover year:', lastYear);
function esriYear(y) {
  y = ee.Number(y);
  return esri.filterDate(ee.Date.fromYMD(y, 1, 1), ee.Date.fromYMD(y.add(1), 1, 1)).mosaic()
    .setDefaultProjection(ee.Projection('EPSG:4326').atScale(10));
}
function to30(img) {
  return img.reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 64})
    .reproject({crs: 'EPSG:4326', scale: 30}).gte(0.5);
}
var built22 = to30(esriYear(2022).eq(7));
var builtNow = to30(esriYear(lastYear).eq(7));
var newBuilt = builtNow.and(built22.not());
var flood30 = to30(flood);

// console check: flooded area in km2 (coarse)
print('Flood area km2 (1 km estimate):',
  ee.Image.pixelArea().divide(1e6).updateMask(flood30)
    .reduceRegion({reducer: ee.Reducer.sum(), geometry: pak, scale: 1000, maxPixels: 1e10}).values());

// ---- district table ----
var area = ee.Image.pixelArea().divide(1e6);
var out = ee.Image.cat([
  area.updateMask(flood30).rename('flood_km2'),
  area.updateMask(newBuilt).rename('newbuilt_km2'),
  area.updateMask(newBuilt.and(flood30)).rename('newbuilt_in_flood_km2'),
  area.updateMask(built22.and(flood30)).rename('built22_in_flood_km2')
]).reduceRegions({collection: districts, reducer: ee.Reducer.sum(), scale: 30, tileScale: 4})
  .map(function(f) { return f.setGeometry(null).set('last_year', lastYear); });
Export.table.toDrive({collection: out, description: 'pak_flood_rebuild', folder: 'shumaar', fileFormat: 'CSV'});

// ---- map of the worst-hit belt (northern Sindh / south Punjab), 30 m ----
// Bands: flood (2022 water), built22, newbuilt. One byte each.
var box = ee.Geometry.Rectangle([67.0, 26.0, 70.5, 29.0]);
var img = flood30.unmask(0).toByte().rename('flood')
  .addBands(built22.unmask(0).toByte().rename('built22'))
  .addBands(newBuilt.unmask(0).toByte().rename('newbuilt'));
Export.image.toDrive({
  image: img.clip(box), description: 'flood_rebuild_sindh', folder: 'shumaar',
  region: box, crs: 'EPSG:4326', scale: 30, maxPixels: 1e9, fileFormat: 'GeoTIFF'
});
