Ext.define('MainHub.components.MonthPicker', {
  extend: 'Ext.form.field.Date',
  alias: 'widget.parkourmonthpicker',

  noDayPicker: true,

  fieldLabel: 'Select Month',
  format: 'F Y',
  submitFormat: 'm/d/Y',
  value: new Date(),
  startDay: 1,

  initComponent: function () {
    this.callParent(arguments);

    this.on('boxready', function (df, e) {
      var dp = df.getPicker();
      dp.on('show', function () {
        dp.showMonthPicker(false);
      });
    });
  }
});
