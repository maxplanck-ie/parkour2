Ext.define('MainHub.model.invoicing.Request', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'request',
      type: 'string'
    },
    {
      name: 'cost_unit',
      type: 'string'
    },
    {
      name: 'sequencer',
      type: 'auto'
    },
    {
      name: 'flowcell',
      type: 'auto'
    },
    {
      name: 'pool',
      type: 'auto'
    },
    {
      name: 'percentage',
      type: 'auto'
    },
    {
      name: 'read_length',
      type: 'auto'
    },
    {
      name: 'num_libraries_samples_show',
      type: 'string'
    },
    {
      name: 'library_protocol',
      type: 'string'
    },
    {
      name: 'fixed_costs',
      type: 'float'
    },
    {
      name: 'sequencing_costs',
      type: 'float'
    },
    {
      name: 'preparation_costs',
      type: 'float'
    },
    {
      name: 'variable_costs',
      type: 'float'
    },
    {
      name: 'total_costs',
      type: 'float'
    }
  ]
});
