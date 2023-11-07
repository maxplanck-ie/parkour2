Ext.define('MainHub.model.metadataexporter.Sample', {
  extend: 'MainHub.model.Base',

  fields: [
    // Common
    {
      name: 'status',
      type: 'string',
      defaultValue: 'add'
    },
    {
      name: 'accession',
      type: 'string',
      defaultValue: 'update_by_ENA'
    },
    {
      name: 'submission_date',
      type: 'string',
      defaultValue: 'update_by_ENA'
    },
    {
      type: 'bool',
      name: 'invalid',
      defaultValue: false
    },
    {
      type: 'auto',
      name: 'errors',
      defaultValue: {}
    },

    // Experiments
    {
      name: 'pk',
      type: 'int'
    },
    {
      name: 'barcode',
      type: 'string'
    },
    {
      name: 'library_name',
      type: 'string'
    },
    {
      name: 'library_strategy',
      type: 'string'
    },
    {
      name: 'design_description',
      type: 'string'
    },
    {
      name: 'library_source',
      type: 'string'
    },
    {
      name: 'library_selection',
      type: 'string'
    },
    {
      name: 'library_layout',
      type: 'string'
    },
    {
      name: 'insert_size',
      type: 'int',
      allowNull: true
    },
    {
      name: 'library_construction_protocol',
      type: 'string'
    },
    {
      name: 'platform',
      type: 'string',
      defaultValue: 'Illumina'
    },
    {
      name: 'instrument_model',
      type: 'string'
    },

    // Samples
    {
      name: 'scientific_name',
      type: 'string'
    },
    {
      name: 'taxon_id',
      type: 'int',
      allowNull: true
    },
    {
      name: 'title',
      type: 'string'
    },
    {
      name: 'sample_description',
      type: 'string'
    },

    // Runs
    {
      name: 'file_name',
      type: 'string'
    },
    {
      name: 'file_format',
      type: 'string'
    },
    {
      name: 'file_checksum',
      type: 'string',
      defaultValue: 'update_by_ENA'
    }
  ],

  validators: {
    library_name: [
      {
        type: 'presence'
      },
      {
        type: 'unique',  // Defined in `model/libraries/BatchAdd/Common.js`
        dataIndex: 'library_name'
      }
    ],
    library_strategy: 'presence',
    design_description: 'presence',
    library_source: 'presence',
    library_selection: 'presence',
    library_layout: 'presence',
    insert_size: 'presence',
    library_construction_protocol: 'presence',
    platform: 'presence',
    instrument_model: 'presence',
    scientific_name: 'presence',
    taxon_id: 'presence',
    title: 'presence',
    sample_description: 'presence',
    file_name: 'presence',
    file_format: 'presence'
  }
});
