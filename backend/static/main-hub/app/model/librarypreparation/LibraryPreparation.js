Ext.define("MainHub.model.librarypreparation.LibraryPreparation", {
  extend: "MainHub.model.Record",

  fields: [
    {
      name: "pk",
      type: "int"
    },
    {
      name: "name",
      type: "string"
    },
    {
      name: "is_converted",
      type: "bool"
    },
    {
      name: "barcode",
      type: "string"
    },
    {
      name: "create_time",
      type: "date"
    },
    {
      name: "request_name",
      type: "string"
    },
    {
      name: "pool_name",
      type: "string"
    },
    {
      name: "selected",
      type: "bool",
      defaultValue: false
    },
    {
      name: "comments_facility",
      type: "string"
    },
    {
      name: "comments",
      type: "string"
    },
    {
      name: "library_protocol",
      type: "int"
    },
    {
      name: "library_protocol_name",
      type: "string"
    },
    {
      name: "concentration_sample",
      type: "float",
      allowNull: true
    },
    {
      name: "starting_amount",
      type: "float",
      allowNull: true
    },
    {
      name: "spike_in_description",
      type: "string"
    },
    {
      name: "spike_in_volume",
      type: "float",
      allowNull: true
    },
    {
      name: "coordinate",
      type: "string"
    },
    {
      name: "index_i7_id",
      type: "string"
    },
    {
      name: "index_i5_id",
      type: "string"
    },
    {
      name: "pcr_cycles",
      type: "int",
      allowNull: true
    },
    {
      name: "concentration_library",
      type: "float",
      allowNull: true
    },
    {
      name: "mean_fragment_size",
      type: "int",
      allowNull: true
    },
    {
      name: "nM",
      type: "float",
      allowNull: true
    },
    {
      name: "dilution_factor",
      type: "int",
      allowNull: true
    },
    {
      name: "quality_check",
      type: "string",
      allowNull: true
    },
    {
      name: "smear_analysis",
      type: "float"
    }
  ]
});
