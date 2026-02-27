function applyColorNameBackgrounds() {
  var ss = SpreadsheetApp.getActive();
  var sheet = ss.getSheetByName('school_buses');

  if (!sheet) {
    throw new Error('Sheet not found: school_buses');
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    Logger.log('No data rows found.');
    return;
  }

  // Columns:
  // D = color_name
  // E = hex_color
  var startRow = 2;
  var numRows = lastRow - 1;

  var hexRange = sheet.getRange(startRow, 5, numRows, 1); // E
  var colorNameRange = sheet.getRange(startRow, 4, numRows, 1); // D

  var hexValues = hexRange.getValues(); // [[...], ...]
  var backgrounds = [];

  for (var i = 0; i < hexValues.length; i++) {
    var raw = hexValues[i][0];

    if (raw === null || raw === undefined) {
      backgrounds.push(['']);
      continue;
    }

    var hex = String(raw).trim();

    // Accept '#RRGGBB' only
    if (!/^#[0-9A-Fa-f]{6}$/.test(hex)) {
      backgrounds.push(['']);
      continue;
    }

    backgrounds.push([hex]);
  }

  colorNameRange.setBackgrounds(backgrounds);
}
