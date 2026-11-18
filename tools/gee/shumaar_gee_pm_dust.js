// Shumaar: how much of each district's PM2.5 is dust and sea salt, 2000-2025, for Google Earth Engine.
// The PM2.5 layer on the site (ACAG/WashU) is total PM2.5, which is what monitors and WHO measure.
// This script estimates the dust and sea-salt part from NASA MERRA-2 aerosol reanalysis, so the site can
// also show PM2.5 excluding dust and sea salt (the human-made part policy can act on).
//
// 1. Paste into a NEW script and click Run.
// 2. In Tasks, Run the export pak_pm_dust (a few minutes to an hour). Send back the CSV.
//
// MERRA-2 surface mass concentrations (kg/m3, converted to ug/m3), ~50 km grid:
//   DUSMASS25 dust < 2.5 um, SSSMASS25 sea salt < 2.5 um, BCSMASS black carbon,
//   OCSMASS organic carbon (x1.4 for organic matter), SO4SMASS sulphate (x1.375 for ammonium sulphate).
// MERRA-2 has no nitrate, so the dust share will read somewhat high in winter in Punjab.

var districts = ee.FeatureCollection('projects/shumaar-514920/assets/shumaar_districts_shp');
var col = ee.ImageCollection('NASA/GSFC/MERRA/aer/2')
  .select(['DUSMASS25', 'SSSMASS25', 'BCSMASS', 'OCSMASS', 'SO4SMASS']);

function period(start, end, label, season) {
  var img = col.filterDate(start, end).mean().multiply(1e9); // kg/m3 -> ug/m3
  img = img.addBands(img.select('OCSMASS').multiply(1.4).rename('OM'))
           .addBands(img.select('SO4SMASS').multiply(1.375).rename('SO4'));
  img = img.select(['DUSMASS25', 'SSSMASS25', 'BCSMASS', 'OM', 'SO4'], ['dust', 'seasalt', 'bc', 'om', 'so4']);
  return img.reduceRegions({collection: districts, reducer: ee.Reducer.mean(), scale: 10000, tileScale: 2})
    .map(function(f) { return f.setGeometry(null).set({year: label, season: season}); });
}

var years = ee.List.sequence(2000, 2025);
var annual = ee.FeatureCollection(years.map(function(y) {
  var s = ee.Date.fromYMD(y, 1, 1);
  return period(s, s.advance(1, 'year'), y, 'year');
})).flatten();

// Seasons for 2021-2025 combined: winter smog (Nov-Jan) and pre-monsoon dust (Apr-Jun)
var seas = ee.FeatureCollection(ee.List.sequence(2021, 2025).map(function(y) {
  y = ee.Number(y);
  var w = period(ee.Date.fromYMD(y.subtract(1), 11, 1), ee.Date.fromYMD(y, 2, 1), y, 'nov-jan');
  var d = period(ee.Date.fromYMD(y, 4, 1), ee.Date.fromYMD(y, 7, 1), y, 'apr-jun');
  return w.merge(d);
})).flatten();

Export.table.toDrive({
  collection: annual.merge(seas), description: 'pak_pm_dust', folder: 'shumaar', fileFormat: 'CSV',
  selectors: ['id', 'n', 'p', 'year', 'season', 'dust', 'seasalt', 'bc', 'om', 'so4']
});
