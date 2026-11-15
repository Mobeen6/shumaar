// Shumaar: "The city beyond the line" - built-up land around Pakistan's 20 biggest cities, 1990-latest,
// plus farmland turned into built-up land by district. For Google Earth Engine.
//
// 1. Paste into a NEW script and click Run. The Console prints the latest land-cover year and the city list.
// 2. In Tasks you will see 21 exports: 20 city maps (city_<name>) and one table (pak_farmland_to_builtup).
//    Click Run on each (the defaults are fine). They land in Google Drive / folder "shumaar".
//    Tip: the table is the slowest; start it first.
// 3. Send back all 21 files (the .tif files and the .csv).
//
// Data
//   GAIA (Gong et al. 2020, Remote Sensing of Environment): year a 30 m pixel first became impervious, 1985-2018.
//   Esri / Impact Observatory 10 m land cover (Karra et al. 2021), annual 2017-latest: classes 5 = crops, 7 = built area.

var districts = ee.FeatureCollection('projects/shumaar/assets/shumaar_districts_shp');

// ---- built-up layers -------------------------------------------------------
var gaia = ee.Image('Tsinghua/FROM-GLC/GAIA/v10').select('change_year_index'); // 1 = 2018 ... 34 = 1985
var esri = ee.ImageCollection('projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS');
var lastYear = ee.Date(esri.aggregate_max('system:time_start')).get('year');
print('Latest Esri land-cover year:', lastYear);

function esriYear(y) {
  y = ee.Number(y);
  return esri.filterDate(ee.Date.fromYMD(y, 1, 1), ee.Date.fromYMD(y.add(1), 1, 1)).mosaic()
    .setDefaultProjection(ee.Projection('EPSG:4326').atScale(10));
}
var lcLast = esriYear(lastYear);
var lc2017 = esriYear(2017);
var builtLast10 = lcLast.eq(7);
var crop2017_10 = lc2017.eq(5);

// 10 m -> 30 m: share of the 30 m cell that is built / cropland
function to30(img) {
  return img.reduceResolution({reducer: ee.Reducer.mean(), maxPixels: 64})
    .reproject({crs: 'EPSG:4326', scale: 30});
}
var builtLast = to30(builtLast10).gte(0.5);
var crop2017 = to30(crop2017_10).gte(0.5);

// Band "epoch": 1 built by 1990, 2 by 2000, 3 by 2010, 4 by 2018 (GAIA), 5 built in the latest Esri year only, 0 not built.
var b1990 = gaia.gte(29), b2000 = gaia.gte(19), b2010 = gaia.gte(9), b2018 = gaia.gte(1);
var epoch = ee.Image(0)
  .where(builtLast, 5)
  .where(b2018, 4).where(b2010, 3).where(b2000, 2).where(b1990, 1)
  .unmask(0).toByte().rename('epoch');
var stack = epoch.addBands(crop2017.unmask(0).toByte().rename('crop2017'))
  .addBands(builtLast.unmask(0).toByte().rename('built_last'));

// ---- the 20 largest cities (Census 2023), centre point and half-width of the box in km ----
var cities = [
  ['Karachi', 67.03, 24.90, 40], ['Lahore', 74.33, 31.52, 35], ['Faisalabad', 73.08, 31.42, 25],
  ['Rawalpindi_Islamabad', 73.06, 33.65, 30], ['Gujranwala', 74.19, 32.16, 30], ['Peshawar', 71.53, 34.01, 25],
  ['Multan', 71.47, 30.20, 25], ['Hyderabad', 68.37, 25.39, 25], ['Quetta', 66.99, 30.19, 25],
  ['Bahawalpur', 71.68, 29.39, 20], ['Sargodha', 72.67, 32.08, 20], ['Sialkot', 74.53, 32.49, 20],
  ['Sukkur', 68.86, 27.71, 20], ['Larkana', 68.21, 27.56, 20], ['Sheikhupura', 73.98, 31.71, 20],
  ['Rahim_Yar_Khan', 70.30, 28.42, 20], ['Jhang', 72.32, 31.27, 20], ['Dera_Ghazi_Khan', 70.64, 30.05, 20],
  ['Gujrat', 74.08, 32.57, 20], ['Mardan', 72.05, 34.20, 20]
];
cities.forEach(function(c) {
  var lat = c[2], hw = c[3];
  var dLat = hw / 111.32, dLon = hw / (111.32 * Math.cos(lat * Math.PI / 180));
  var box = ee.Geometry.Rectangle([c[1] - dLon, lat - dLat, c[1] + dLon, lat + dLat]);
  Export.image.toDrive({
    image: stack.clip(box), description: 'city_' + c[0], folder: 'shumaar',
    region: box, crs: 'EPSG:4326', scale: 30, maxPixels: 1e9, fileFormat: 'GeoTIFF'
  });
});
print('Cities:', cities.map(function(c) { return c[0]; }));

// ---- farmland turned into built-up land, by district, at 10 m ---------------
var area = ee.Image.pixelArea().divide(1e6); // km2
var lost = crop2017_10.and(builtLast10);
var dist = ee.Image.cat([
  area.updateMask(builtLast10).rename('built_last_km2'),
  area.updateMask(lc2017.eq(7)).rename('built_2017_km2'),
  area.updateMask(crop2017_10).rename('crop_2017_km2'),
  area.updateMask(lost).rename('crop_to_built_km2')
]).reduceRegions({collection: districts, reducer: ee.Reducer.sum(), scale: 10, tileScale: 16})
  .map(function(f) { return f.setGeometry(null).set('last_year', lastYear); });
Export.table.toDrive({collection: dist, description: 'pak_farmland_to_builtup', folder: 'shumaar', fileFormat: 'CSV'});
