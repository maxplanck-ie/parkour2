Ext.define('MainHub.model.invoicing.SequencingCost', {
  extend: 'MainHub.model.invoicing.BaseCost',

  fields: [
    {
      name: 'sequencer',
      type: 'int'
    },
    {
      name: 'read_length',
      type: 'int'
    }
  ]
});
