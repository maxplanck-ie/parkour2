Ext.define("MainHub.view.libraries.LibraryWindow", {
  extend: "Ext.window.Window",

  requires: [
    "MainHub.view.libraries.LibraryWindowController",
    "Ext.ux.FileGridField"
  ],

  controller: "libraries-librarywindow",

  height: 225,
  width: 400,

  modal: true,
  resizable: false,
  layout: "fit",

  items: [
    {
      xtype: "panel",
      id: "librarySamplePanel",
      border: 0,
      layout: "card",
      items: [
        {
          xtype: "container",
          layout: {
            type: "vbox",
            align: "center",
            pack: "center"
          },
          defaults: {
            border: 0
          },
          items: [
            {
              xtype: "container",
              layout: "hbox",
              defaultType: "button",
              defaults: {
                margin: 10,
                width: 100,
                height: 40
              },
              items: [
                {
                  id: "libraryCardBtn",
                  itemId: "libraryCardBtn",
                  text: "Library"
                },
                {
                  id: "sampleCardBtn",
                  itemId: "sampleCardBtn",
                  text: "Sample"
                }
              ]
            },
            {
              id: "cardHelpText",
              width: 350,
              html: '<p style="text-align:center">Choose <strong>Library</strong> if samples for sequencing are completely prepared by user.<br><br>Choose <strong>Sample</strong> if libraries are prepared by facility.</p>'
            }
          ]
        },
        {
          xtype: "container",
          id: "libraryCard",
          scrollable: "y",

          items: [
            {
              xtype: "container",
              id: "libraryBarcodeField",
              margin: "15px 15px 0 15px",
              style: {
                padding: "25px 10px 10px 10px",
                border: "1px solid #d0d0d0",
                textAlign: "center",
                fontWeight: "bold",
                fontSize: "50px",
                color: "#757575"
              },
              height: 70,
              hidden: true
            },
            {
              xtype: "form",
              id: "libraryForm",
              itemId: "libraryForm",
              border: 0,
              padding: 15,
              defaultType: "textfield",
              defaults: {
                submitEmptyText: false,
                allowBlank: false,
                labelWidth: 220,
                labelStyle: "padding: 5px 0 0 0",
                anchor: "100%"
              },

              items: [
                {
                  name: "name",
                  id: "libraryName",
                  fieldLabel:
                    'Name <sup><strong><span class="field-tooltip" tooltip-text="Name must be unique for assigned project. Field must contain only A-Za-z0-9 as well as - and _">[?]</span></strong></sup>',
                  emptyText: "Name",
                  regex: new RegExp("^[A-Za-z0-9_-]+$"),
                  regexText: "Only A-Za-z0-9 as well as _ and - are allowed"
                },
                {
                  xtype: "combobox",
                  id: "libraryProtocolField",
                  itemId: "libraryProtocolField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "library_protocol",
                  fieldLabel:
                    'Protocol for Library Preparation <sup><strong><span class="field-tooltip" tooltip-text="Select library construction protocol from predefined list or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Protocol for Library Preparation",
                  store: "libraryProtocolsStore",
                  forceSelection: true
                },
                {
                  xtype: "container",
                  id: "libraryProtocolInfo",
                  margin: "0 0 15px 15px"
                },
                {
                  xtype: "combobox",
                  id: "libraryTypeField",
                  itemId: "libraryTypeField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "library_type",
                  fieldLabel:
                    'Analysis Type <sup><strong><span class="field-tooltip" tooltip-text="Analysis Type is automatically filled based on library construction protocol, if needed select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Analysis Type",
                  store: "libraryTypesStore",
                  forceSelection: true,
                  disabled: true
                },
                {
                  xtype: "numberfield",
                  name: "mean_fragment_size",
                  fieldLabel:
                    'Mean Fragment Size (bp) <sup><strong><span class="field-tooltip" tooltip-text="Specify mean fragments size of library, upload Bioanalyzer or Fragmentanalyzer files">[?]</span></strong></sup>',
                  emptyText: "Mean Fragment Size (bp)",
                  minValue: 0,
                  allowDecimals: false
                },
                {
                  xtype: "combobox",
                  id: "indexType",
                  itemId: "indexType",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "index_type",
                  fieldLabel:
                    'Index Type <sup><strong><span class="field-tooltip" tooltip-text="Select from list with predefined options or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Index Type",
                  store: "IndexTypes",
                  forceSelection: true
                },
                {
                  xtype: "combobox",
                  id: "indexReadsField",
                  itemId: "indexReadsField",
                  queryMode: "local",
                  displayField: "num",
                  valueField: "num",
                  name: "index_reads",
                  fieldLabel:
                    'Number of Index Reads <sup><strong><span class="field-tooltip" tooltip-text="Number of Index Reads = 0: Libraries do not carry any barcode, no barcode will be read during sequencing.<br/><br/>Number of Index Reads = 1: Single-indexed libraries. Index on adapter P7 will be read during sequencing (true for most applications).<br/><br/>Number of Index Reads = 2: Dual-indexed libraries. Index on Adapter P7 and P5 will be read. (i.e Nextera libraries or if a high degree of multiplexing is needed)">[?]</span></strong></sup>',
                  emptyText: "Number of Index Reads",
                  forceSelection: true,
                  disabled: true,
                  store: Ext.create("Ext.data.Store", {
                    fields: [
                      {
                        name: "num",
                        type: "int"
                      }
                    ],
                    data: []
                  })
                },
                {
                  xtype: "combobox",
                  queryMode: "local",
                  displayField: "name",
                  displayTpl: Ext.create(
                    "Ext.XTemplate",
                    '<tpl for=".">',
                    "{index}",
                    "</tpl>"
                  ),
                  valueField: "index",
                  name: "index_i7",
                  id: "indexI7Field",
                  itemId: "indexI7Field",
                  fieldLabel:
                    'Index 1 (I7) <sup><strong><span class="field-tooltip" tooltip-text="Select from predefined list; make sure the displayed index is the sequence used for barcoding. Or enter sequence of index used for barcoding (typically 6 nucleotides)">[?]</span></strong></sup>',
                  emptyText: "Index 1 (I7)",
                  regex: new RegExp(
                    "^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"
                  ),
                  regexText:
                    "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
                  store: "indexI7Store",
                  disabled: true
                },
                {
                  xtype: "combobox",
                  queryMode: "local",
                  displayField: "name",
                  displayTpl: Ext.create(
                    "Ext.XTemplate",
                    '<tpl for=".">',
                    "{index}",
                    "</tpl>"
                  ),
                  valueField: "index",
                  name: "index_i5",
                  id: "indexI5Field",
                  itemId: "indexI5Field",
                  fieldLabel:
                    'Index 2 (I5) <sup><strong><span class="field-tooltip" tooltip-text="Select from predefined list; make sure the displayed index is the sequence used for barcoding. Or enter sequence of index used for barcoding (typically 6 nucleotides)">[?]</span></strong></sup>',
                  emptyText: "Index 2 (I5)",
                  regex: new RegExp(
                    "^(?=(?:.{6}|.{8}|.{10}|.{12}|.{24})$)[ATCG]+$"
                  ),
                  regexText:
                    "Only A, T, C and G (uppercase) are allowed. Index length must be 6, 8, 10, 12 or 24.",
                  store: "indexI5Store",
                  disabled: true
                },
                {
                  xtype: "combobox",
                  id: "readLengthField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "read_length",
                  fieldLabel:
                    'Read Length <sup><strong><span class="field-tooltip" tooltip-text="Select from list with predefined options or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Read Length",
                  store: "readLengthsStore",
                  forceSelection: true
                },
                {
                  xtype: "numberfield",
                  name: "sequencing_depth",
                  fieldLabel: "Sequencing Depth (M)",
                  emptyText: "Sequencing Depth (M)",
                  minValue: 1,
                  allowDecimals: false
                },
                {
                  xtype: "combobox",
                  id: "organismField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "organism",
                  fieldLabel:
                    'Organism <sup><strong><span class="field-tooltip" tooltip-text="Select from list with predefined options or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Organism",
                  store: "organismsStore",
                  forceSelection: true
                },
                {
                  xtype: "textarea",
                  name: "comments",
                  fieldLabel: "Comments",
                  emptyText: "Comments",
                  allowBlank: true,
                  height: 150
                }
              ]
            }
          ]
        },
        {
          xtype: "container", // Sample card
          id: "sampleCard",
          scrollable: "y",

          items: [
            {
              xtype: "container",
              id: "sampleBarcodeField",
              margin: "15px 15px 0 15px",
              style: {
                padding: "25px 10px 10px 10px",
                border: "1px solid #d0d0d0",
                textAlign: "center",
                fontWeight: "bold",
                fontSize: "50px",
                color: "#757575"
              },
              height: 70,
              hidden: true
            },
            {
              xtype: "form",
              id: "sampleForm",
              itemId: "sampleForm",
              border: 0,
              padding: 15,
              defaultType: "textfield",
              defaults: {
                submitEmptyText: false,
                allowBlank: false,
                labelWidth: 220,
                labelStyle: "padding: 5px 0 0 0",
                anchor: "100%"
              },

              items: [
                {
                  name: "name",
                  id: "sampleName",
                  fieldLabel:
                    'Name <sup><strong><span class="field-tooltip" tooltip-text="Name must be unique for assigned project. Field must contain only A-Za-z0-9 as well as - and _">[?]</span></strong></sup>',
                  emptyText: "Name",
                  regex: new RegExp("^[A-Za-z0-9_-]+$"),
                  regexText: "Only A-Za-z0-9 as well as _ and - are allowed"
                },
                {
                  xtype: "combobox",
                  id: "nucleicAcidTypeField",
                  itemId: "nucleicAcidTypeField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "nucleic_acid_type",
                  fieldLabel:
                    'Input Type <sup><strong><span class="field-tooltip" tooltip-text="Select Input Type of your sample or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Input Type",
                  store: "nucleicAcidTypesStore",
                  forceSelection: true
                },
                {
                  xtype: "combobox",
                  id: "sampleProtocolField",
                  itemId: "sampleProtocolField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "library_protocol",
                  fieldLabel:
                    'Protocol for Library Preparation <sup><strong><span class="field-tooltip" tooltip-text="Select library construction protocol from predefined list or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Protocol for Library Preparation",
                  store: "libraryProtocolsStore",
                  forceSelection: true,
                  disabled: true
                },
                {
                  xtype: "container",
                  id: "sampleProtocolInfo",
                  margin: "0 0 15px 15px"
                },
                {
                  xtype: "combobox",
                  id: "sampleTypeField",
                  itemId: "sampleTypeField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "library_type",
                  fieldLabel:
                    'Library Type <sup><strong><span class="field-tooltip" tooltip-text="Library Type is automatically filled based on library construction protocol, if needed select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Analysis Type",
                  store: "libraryTypesStore",
                  forceSelection: true,
                  disabled: true
                },
                {
                  xtype: "combobox",
                  id: "rnaQualityField",
                  itemId: "rnaQualityField",
                  queryMode: "local",
                  valueField: "value",
                  displayField: "name",
                  displayTpl: Ext.create(
                    "Ext.XTemplate",
                    '<tpl for=".">{value}</tpl>'
                  ),
                  name: "rna_quality",
                  fieldLabel:
                    'RNA Quality (RIN, RQN) <sup><strong><span class="field-tooltip" tooltip-text="Select a number from 1 to 10 or select determined by facility">[?]</span></strong></sup>',
                  emptyText: "RNA Quality (RIN, RQN)",
                  store: "rnaQualityStore",
                  regex: new RegExp("^(11|10|[1-9]?(.[0-9]+)?|.[0-9]+)$"),
                  regexText: "Only values between 1 and 10 are allowed.",
                  disabled: true
                },
                {
                  xtype: "combobox",
                  id: "readLengthSampleField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "read_length",
                  fieldLabel:
                    'Read Length <sup><strong><span class="field-tooltip" tooltip-text="Select from list with predefined options or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Read Length",
                  store: "readLengthsStore",
                  forceSelection: true
                },
                {
                  xtype: "numberfield",
                  name: "sequencing_depth",
                  fieldLabel: "Sequencing Depth (M)",
                  emptyText: "Sequencing Depth (M)",
                  minValue: 1,
                  allowDecimals: false
                },
                {
                  xtype: "combobox",
                  id: "organismSampleField",
                  queryMode: "local",
                  displayField: "name",
                  valueField: "id",
                  name: "organism",
                  fieldLabel:
                    'Organism <sup><strong><span class="field-tooltip" tooltip-text="Select from list with predefined options or select other and specify in the comments field (below)">[?]</span></strong></sup>',
                  emptyText: "Organism",
                  store: "organismsStore",
                  forceSelection: true
                },
                {
                  xtype: "textarea",
                  name: "comments",
                  fieldLabel: "Comments",
                  emptyText: "Comments",
                  allowBlank: true,
                  height: 150
                }
              ]
            }
          ]
        }
      ]
    }
  ],

  dockedItems: [
    {
      xtype: "toolbar",
      dock: "bottom",
      items: [
        "->",
        {
          xtype: "button",
          itemId: "saveAndAddWndBtn",
          id: "saveAndAddWndBtn",
          text: "Save and Add another",
          iconCls: "fa fa-floppy-o fa-lg",
          hidden: true
        },
        {
          xtype: "button",
          itemId: "addWndBtn",
          id: "addWndBtn",
          text: "Save and Close",
          iconCls: "fa fa-floppy-o fa-lg",
          hidden: true
        }
      ],
      hidden: true
    }
  ]
});
