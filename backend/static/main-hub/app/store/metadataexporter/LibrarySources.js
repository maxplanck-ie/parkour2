Ext.define('MainHub.store.metadataexporter.LibrarySources', {
  extend: 'Ext.data.Store',
  storeId: 'ENALibrarySources',

  fields: [
    {
      name: 'name',
      type: 'string'
    }
  ],

  data: [
    {
      name: 'genomic'
    },
    {
      name: 'genomic single cell'
    },
    {
      name: 'transcriptomic'
    },
    {
      name: 'transcriptomic single cell'
    },
    {
      name: 'metagenomic'
    },
    {
      name: 'metatranscriptomic'
    },
    {
      name: 'synthetic'
    },
    {
      name: 'viral rna'
    },
    {
      name: 'other'
    }
  ]
});
