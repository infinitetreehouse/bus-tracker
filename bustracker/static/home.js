document.addEventListener('DOMContentLoaded', function () {
  var grid = document.getElementById('bus_checkbox_grid');
  var btnAll = document.getElementById('bus_select_all');
  var btnClear = document.getElementById('bus_clear_all');

  if (!grid || !btnAll || !btnClear) {
    return;
  }

  function setAll(isChecked) {
    var boxes = grid.querySelectorAll('input[type="checkbox"][name="bus_codes"]');
    for (var i = 0; i < boxes.length; i++) {
      boxes[i].checked = isChecked;
    }
  }

  btnAll.addEventListener('click', function () {
    setAll(true);
  });

  btnClear.addEventListener('click', function () {
    setAll(false);
  });
});
