Ext.define('MainHub.mixins.grid.CheckboxesAndSearchInput', {
  changeFilter: function (el, value) {
    var grid = el.up('grid');
    var store = grid.getStore();
    var columns = Ext.pluck(grid.getColumns(), 'dataIndex');
    var showLibraries = null;
    var showSamples = null;
    var searchQuery = null;

    if (el.itemId === 'show-libraries-checkbox') {
      showLibraries = value;
      showSamples = el.up().items.items[1].getValue();
      searchQuery = el.up('header').down('textfield').getValue();
    } else if (el.itemId === 'show-samples-checkbox') {
      showLibraries = el.up().items.items[0].getValue();
      showSamples = value;
      searchQuery = el.up('header').down('textfield').getValue();
    } else if (el.itemId === 'search-field') {
      showLibraries = el.up().down('fieldcontainer').items.items[0].getValue();
      showSamples = el.up().down('fieldcontainer').items.items[1].getValue();
      searchQuery = value;
    }

    var showFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (record.get('record_type') === 'Library') {
          res = res || showLibraries;
        } else {
          res = res || showSamples;
        }
        return res;
      }
    });

    var searchFilter = Ext.util.Filter({
      filterFn: function (record) {
        var res = false;
        if (searchQuery) {
          Ext.each(columns, function (column) {
            var val = record.get(column);
            if (val && val.toString().toLowerCase().indexOf(searchQuery.toLowerCase()) > -1) {
              res = res || true;
            }
          });
        } else {
          res = true;
        }
        return res;
      }
    });

    store.clearFilter();
    store.filter([showFilter, searchFilter]);
  }
});
