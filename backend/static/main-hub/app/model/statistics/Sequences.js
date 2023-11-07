Ext.define('MainHub.model.statistics.Sequences', {
  extend: 'MainHub.model.Base',

  fields: [
    {
      name: 'pk',
      type: 'int'
    },
    {
      name: 'flowcell_id',
      type: 'string'
    },
    {
      name: 'create_time',
      type: 'date'
    },
    {
      name: 'sequencer',
      type: 'string'
    },
    {
      name: 'request',
      type: 'string'
    },
    {
      name: 'barcode',
      type: 'string'
    },
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'lane',
      type: 'string'
    },
    {
      name: 'pool',
      type: 'string'
    },
    {
      name: 'library_protocol',
      type: 'string'
    },
    {
      name: 'library_type',
      type: 'string'
    },
    {
      name: 'reads_pf_requested',
      type: 'float',
      allowNull: true
    },
    {
      name: 'reads_pf_sequenced',
      type: 'float',
      allowNull: true
    },
    {
      name: 'confident_reads',
      type: 'float',
      allowNull: true
    },
    {
      name: 'optical_duplicates',
      type: 'float',
      allowNull: true
    },
    {
      name: 'dupped_reads',
      type: 'float',
      allowNull: true
    },
    {
      name: 'mapped_reads',
      type: 'float',
      allowNull: true
    },
    {
      name: 'insert_size',
      type: 'float',
      allowNull: true
    }
  ]
});
