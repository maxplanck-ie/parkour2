Ext.define('MainHub.store.metadataexporter.LibrarySelections', {
  extend: 'Ext.data.Store',
  storeId: 'ENALibrarySelections',

  fields: [
    {
      name: 'name',
      type: 'string'
    }
  ],

  data: [
    {
      name: 'random'
    },
    {
      name: 'pcr'
    },
    {
      name: 'random pcr'
    },
    {
      name: 'rt-pcr'
    },
    {
      name: 'hmpr'
    },
    {
      name: 'mf'
    },
    {
      name: 'repeat fractionation'
    },
    {
      name: 'size fractionation'
    },
    {
      name: 'msll'
    },
    {
      name: 'cdna'
    },
    {
      name: 'cdna_randompriming'
    },
    {
      name: 'cdna_oligo_dt'
    },
    {
      name: 'polya'
    },
    {
      name: 'oligo-dt'
    },
    {
      name: 'inverse rrna'
    },
    {
      name: 'inverse rrna selection'
    },
    {
      name: 'chip'
    },
    {
      name: 'mnase'
    },
    {
      name: 'dnase'
    },
    {
      name: 'hybrid selection'
    },

    {
      name: 'reduced representation'
    },
    {
      name: 'restriction digest'
    },
    {
      name: '5-methylcytidine antibody'
    },
    {
      name: 'mbd2 protein methyl-cpg binding domain'
    },
    {
      name: 'cage'
    },
    {
      name: 'race'
    },
    {
      name: 'mda'
    },
    {
      name: 'padlock probes capture method'
    },
    {
      name: 'other'
    },
    {
      name: 'unspecified'
    }
  ]
});
