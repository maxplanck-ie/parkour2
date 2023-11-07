Ext.define('MainHub.view.usage.ChartPolarBase', {
  extend: 'Ext.chart.PolarChart',
  xtype: 'parkourpolar',

  border: 0,

  // theme: 'sky',

  colors: [
    '#5DA5DA',
    '#FAA43A',
    '#60BD68',
    '#F17CB0',
    '#B2912F',
    '#B276B2',
    '#DECF3F',
    '#F15854',
    '#4D4D4D'
  ],

  // colors: [
  //   '#8dd3c7',
  //   '#ffffb3',
  //   '#bebada',
  //   '#fb8072',
  //   '#80b1d3',
  //   '#fdb462',
  //   '#b3de69',
  //   '#fccde5',
  //   '#d9d9d9',
  //   '#bc80bd',
  //   '#ccebc5',
  //   '#ffed6f'
  // ],

  insetPadding: 40,
  innerPadding: 10,

  interactions: ['rotate', 'itemhighlight'],

  // legend: {
  //   docked: 'right'
  // },

  series: {
    type: 'pie',
    highlight: true,
    angleField: 'data',
    donut: 20,
    label: {
      field: 'name',
      display: 'outside',
      contrast: true,
      // font: '14px Open Sans',
      color: '#606060',
      calloutLine: {
        length: 50,
        width: 3
      }
    },
    tooltip: {
      trackMouse: true,
      renderer: function (toolTip, record, ctx) {
        toolTip.setHtml(record.get('name') + ': ' + record.get('data'));
      }
    }
  }
});
