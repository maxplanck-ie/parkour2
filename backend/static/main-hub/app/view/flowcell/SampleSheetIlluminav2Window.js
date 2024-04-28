Ext.define("MainHub.view.flowcell.SampleSheetIlluminav2Window", {
  extend: "Ext.window.Window",
  requires: ["MainHub.view.flowcell.SampleSheetIlluminav2WindowController"],

  controller: "flowcell-samplesheet-illuminav2-window",

  title: "Sample Sheet Generator - Illumina v2",
  modal: true,
  autoShow: true,

  width: 580,
  height: 575,
  layout: "fit",

  items: [
    {
      xtype: "form",
      id: "ss-options-form",
      padding: "15 15 0 15",
      border: 0,
      autoScroll: true,
      defaults: {
        width: 520,
        labelWidth: 140,
      },
      items: [
        {
          xtype: "label",
          html: "Only the fields marked in <b>bold</b> are required.",
        },
        {
          xtype: "fieldset",
          title: "Header",
          defaults: {
            width: 490,
            labelWidth: 140,
          },
          items: [
            {
              xtype: "textfield",
              name: "SS-Header-RunName",
              fieldLabel: "<b>Run Name</b>",
              regex: /^[A-Za-z0-9_]+$/,
              regexText: "Only A-Z a-z 0-9 and _ are allowed",
              allowBlank: false,
            },
          ],
        },
        {
          xtype: "fieldset",
          title: "Reads",
          defaults: {
            width: 490,
            labelWidth: 140,
          },
          items: [
            {
              xtype: "fieldcontainer",
              layout: "hbox",
              fieldLabel: "Read Cycles",
              labelSeparator: "",
              defaults: {
                xtype: "numberfield",
                allowDecimals: false,
                labelWidth: 20,
                flex: 1,
                value: null,
                minValue: 0,
                hideTrigger: true,
                padding: "0 0 0 5",
              },
              items: [
                {
                  name: "SS-Reads-Read1Cycles",
                  fieldLabel:
                    '<span data-qtip="Read 1" style="font-weight:bold;">R1</span>',
                  value: 30,
                  minValue: 1,
                  allowBlank: false,
                  padding: 0,
                },
                {
                  name: "SS-Reads-Read2Cycles",
                  fieldLabel: '<span data-qtip="Read 2">R2</span>',
                },
                {
                  name: "SS-Reads-Index1Cycles",
                  fieldLabel: '<span data-qtip="Index 1">I1</span>',
                },
                {
                  name: "SS-Reads-Index2Cycles",
                  fieldLabel: '<span data-qtip="Index 2">I2</span>',
                },
              ],
            },
          ],
        },
        {
          xtype: "fieldset",
          title: "Sequencing Settings",
          defaults: {
            width: 490,
            labelWidth: 140,
          },
          items: [
            {
              xtype: "fieldcontainer",
              layout: "hbox",
              fieldLabel: "Custom primer",
              labelSeparator: "",
              defaults: {
                xtype: "checkbox",
                labelWidth: 20,
                flex: 1,
                value: false,
                inputValue: "true",
              },
              items: [
                {
                  name: "SS-Sequencing_Settings-CustomRead1Primer",
                  fieldLabel: '<span data-qtip="Read 1">R1</span>',
                },
                {
                  name: "SS-Sequencing_Settings-CustomRead2Primer",
                  fieldLabel: '<span data-qtip="Read 2">R2</span>',
                },
                {
                  name: "SS-Sequencing_Settings-CustomIndex1Primer",
                  fieldLabel: '<span data-qtip="Index 1">I1</span>',
                },
                {
                  name: "SS-Sequencing_Settings-CustomIndex2Primer",
                  fieldLabel: '<span data-qtip="Index 2">I2</span>',
                },
              ],
            },
            {
              xtype: "combobox",
              name: "SS-Sequencing_Settings-LibraryPrepKits",
              fieldLabel: "Library Prep Kits",
              padding: "10 0 10 0",
              store: Ext.create("Ext.data.Store", {
                fields: ["name"],
                data: [
                  {
                    name: "ILMNStrandedTotalRNA",
                  },
                  {
                    name: "ILMNStrandedmRNA",
                  },
                ],
              }),
              queryMode: "local",
              displayField: "name",
              valueField: "name",
              value: "",
              forceSelection: false,
              allowBlank: true,
            },
          ],
        },
        {
          xtype: "fieldset",
          title: "BCL Settings",
          margin: 0,
          defaults: {
            width: 490,
            labelWidth: 140,
          },
          items: [
            {
              xtype: "fieldcontainer",
              layout: "hbox",
              fieldLabel: "Barcode Mismatches",
              labelSeparator: "",
              defaults: {
                xtype: "numberfield",
                allowDecimals: false,
                minValue: 0,
                value: 1,
                labelWidth: 20,
                flex: 1,
                hideTrigger: true,
              },
              items: [
                {
                  name: "SS-BCLConvert_Settings-BarcodeMismatchesIndex1",
                  fieldLabel: '<span data-qtip="Index 1">I1</span>',
                },
                {
                  name: "SS-BCLConvert_Settings-BarcodeMismatchesIndex2",
                  fieldLabel: '<span data-qtip="Index 2">I2</span>',
                  padding: "0 0 0 5",
                },
              ],
            },
            {
              xtype: "textfield",
              name: "SS-BCLConvert_Settings-FastqCompressionFormat",
              fieldLabel: "FASTQ Compression",
              padding: "10 0 0 0",
              value: "gzip",
              readOnly: true,
            },
            {
              xtype: "textfield",
              name: "SS-BCLConvert_Settings-AdapterRead1",
              fieldLabel: "Adapter Read 1",
              regex: /^[ACGT]+$/,
              regexText: "Only A, T, C ang G are allowed",
            },
            {
              xtype: "textfield",
              name: "SS-BCLConvert_Settings-AdapterRead2",
              fieldLabel: "Adapter Read 2",
              regex: /^[ACGT]+$/,
              regexText: "Only A, T, C ang G are allowed",
            },
            {
              xtype: "fieldcontainer",
              layout: "vbox",
              fieldLabel: "Override Cycles",
              labelSeparator: "",
              items: [
                {
                  xtype: "fieldcontainer",
                  layout: "hbox",
                  labelSeparator: "",
                  defaults: {
                    xtype: "textfield",
                    allowDecimals: false,
                    labelWidth: 20,
                    width: 170,
                    value: null,
                    hideTrigger: true,
                    regex: /^[YUIN0-9]+$/,
                    regexText: "Only Y, U, I, N and 0-9 are allowed",
                  },
                  items: [
                    {
                      name: "OC-BCLConvert_Settings-OverrideCycles-1",
                      fieldLabel: '<span data-qtip="Read 1">R1</span>',
                    },
                    {
                      name: "OC-BCLConvert_Settings-OverrideCycles-2",
                      fieldLabel: '<span data-qtip="Read 2">R2</span>',
                      padding: "0 0 0 5",
                    },
                  ],
                },
                {
                  xtype: "fieldcontainer",
                  layout: "hbox",
                  labelSeparator: "",
                  defaults: {
                    xtype: "textfield",
                    allowDecimals: false,
                    labelWidth: 20,
                    width: 170,
                    value: null,
                    hideTrigger: true,
                    regex: /^[YUIN0-9]+$/,
                    regexText: "Only Y, U, I, N and 0-9 are allowed",
                  },
                  items: [
                    {
                      name: "OC-BCLConvert_Settings-OverrideCycles-3",
                      fieldLabel: '<span data-qtip="Index 1">I1</span>',
                    },
                    {
                      name: "OC-BCLConvert_Settings-OverrideCycles-4",
                      fieldLabel: '<span data-qtip="Index 2">I2</span>',
                      padding: "0 0 0 5px",
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
  ],

  dockedItems: [
    {
      xtype: "toolbar",
      dock: "bottom",
      items: [
        "->",
        {
          xtype: "button",
          itemId: "ss-cancel-button",
          iconCls: "fa fa-ban fa-lg",
          text: "Cancel",
        },
        {
          xtype: "button",
          itemId: "ss-save-button",
          text: "Save",
          iconCls: "fa fa-floppy-o fa-lg",
        },
      ],
    },
  ],
});
