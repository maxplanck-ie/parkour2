Ext.define('MainHub.view.metadataexporter.Samples', {
  extend: 'MainHub.view.metadataexporter.MetadataBaseGrid',
  alias: 'widget.metadata-samples',

  border: 0,

  viewConfig: {
    markDirty: false,
    stripeRows: false,
    getRowClass: function (record) {
      return record.get('invalid') ? 'invalid' : '';
    }
  },

  columns: {
    defaults: {
      minWidth: 150,
      flex: 1,
      editor: {
        xtype: 'textfield',
        allowBlank: false
      },
      renderer: 'errorRenderer'
    },
    items: [
      {
        xtype: 'checkcolumn',
        itemId: 'check-column',
        dataIndex: 'selected',
        renderer: undefined,
        tdCls: 'no-dirty',
        editor: null,
        minWidth: 40,
        width: 40
      },
      // Experiments
      {
        text: 'Library Name',
        dataIndex: 'library_name',
        regex: new RegExp(/^[A-Za-z0-9_-]+$/),
        regexText: 'Only A-Za-z0-9 as well as _ and - are allowed'
      },
      {
        text: 'Library Strategy',
        dataIndex: 'library_strategy',
        tooltip: 'Sequencing technique intended for this library'
      },
      {
        text: 'Design Description',
        dataIndex: 'design_description',
        tooltip: 'Goal and setup of the individual library including library was constructed'
      },
      {
        text: 'Library Source',
        dataIndex: 'library_source',
        tooltip: 'Library Source specifies the type of source material that is being sequenced',
        renderer: 'comboboxErrorRenderer',
        editor: {
          xtype: 'combobox',
          queryMode: 'local',
          displayField: 'name',
          valueField: 'name',
          store: 'ENALibrarySources',
          forceSelection: true
        }
      },
      {
        text: 'Library Selection',
        dataIndex: 'library_selection',
        tooltip: 'Method used to enrich the target in the sequence library preparation',
        renderer: 'comboboxErrorRenderer',
        editor: {
          xtype: 'combobox',
          queryMode: 'local',
          displayField: 'name',
          valueField: 'name',
          store: 'ENALibrarySelections',
          forceSelection: true
        }
      },
      {
        text: 'Library Layout',
        dataIndex: 'library_layout',
        toioltip: 'Library Layout specifies whether to expect single or paired configuration of reads'
      },
      {
        text: 'Insert Size',
        dataIndex: 'insert_size',
        editor: {
          xtype: 'numberfield',
          minValue: 0
        }
      },
      {
        text: 'Library Construction Protocol',
        dataIndex: 'library_construction_protocol',
        tooltip: 'Protocol by which the library was constructed'
      },
      {
        text: 'Platform',
        dataIndex: 'platform',
        tooltip: 'Sequencing platform used in the experiment'
      },
      {
        text: 'Instrument Model',
        dataIndex: 'instrument_model',
        tooltip: 'Sequencing platform model'
      },
      // Samples
      {
        text: 'Scientific Name',
        dataIndex: 'scientific_name',
        tooltip: 'Scientific name of sample that distinguishes its taxonomy. Please use a name or synonym that is tracked in the INSDC Taxonomy database.'
      },
      {
        text: 'Taxon ID',
        dataIndex: 'taxon_id',
        tooltip: 'NCBI Taxonomy Identifier',
        editor: {
          xtype: 'numberfield',
          minValue: 0
        }
      },
      {
        text: 'Sample Title',
        dataIndex: 'title',
        tooltip: 'Short text that can be used to call out sample records in search results or in displays'
      },
      {
        text: 'Sample Description',
        dataIndex: 'sample_description',
        tooltip: 'Free-form text describing the sample, its origin, and its method of isolation'
      },
      // Runs
      {
        text: 'File Name',
        dataIndex: 'file_name'
      },
      {
        text: 'File Format',
        dataIndex: 'file_format'
      }
    ]
  }
});
