Ext.define('MainHub.overrides.grid.plugin.RowEditing', {
  override: 'Ext.grid.plugin.RowEditing',

  activateCell: function (pos) {
    var cell = pos.getCell();

    if (
      cell && !cell.query('[tabIndex="-1"]').length &&
      !cell.hasCls('x-grid-cell-check-column')
    ) {
      this.startEdit(pos.record, pos.column);
      return true;
    }
  }
});
