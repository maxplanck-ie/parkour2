Ext.define('MainHub.overrides.picker.Date', {
  override: 'Ext.picker.Date',

  onOkClick: function (picker, value) {
    var me = this;
    var month = value[0];
    var year = value[1];
    var date = new Date(year, month, me.getActive().getDate());
    var dateField = picker.up('datefield');

    if (date.getMonth() !== month) {
      // 'fix' the JS rolling date conversion if needed
      date = Ext.Date.getLastDateOfMonth(new Date(year, month, 1));
    }
    me.setValue(date);
    me.hideMonthPicker();

    if (dateField && dateField.noDayPicker) {
      dateField.setValue(new Date(date));
      dateField.fireEvent('select', dateField, dateField.value);
      dateField.collapse();
    }
  },

  onCancelClick: function () {
    var dateField = this.up('datefield');

    this.selectedUpdate(this.activeDate);
    this.hideMonthPicker();

    if (dateField && dateField.noDayPicker) {
      dateField.collapse();
    }
  }
});
