Ext.define("MainHub.model.statistics.RunStatistics", {
  extend: "MainHub.model.Base",

  fields: [
    {
      name: "pk",
      type: "int"
    },
    {
      name: "flowcell_id",
      type: "string"
    },
    {
      name: "create_time",
      type: "date"
    },
    {
      name: "sequencer",
      type: "string"
    },
    {
      name: "read_length",
      type: "string"
    },
    {
      name: "name",
      type: "string"
    },
    {
      name: "pool",
      type: "string"
    },
    {
      name: "request",
      type: "string"
    },
    {
      name: "library_preparation",
      type: "string"
    },
    {
      name: "library_type",
      type: "string"
    },
    {
      name: "loading_concentration",
      type: "float",
      allowNull: true
    },
    {
      name: "cluster_pf",
      type: "float",
      allowNull: true
    },
    {
      name: "reads_pf",
      type: "float",
      allowNull: true
    },
    {
      name: "undetermined_indices",
      type: "float",
      allowNull: true
    },
    {
      name: "phix",
      type: "float",
      allowNull: true
    },
    {
      name: "read_1",
      type: "float",
      allowNull: true
    },
    {
      name: "read_2",
      type: "float",
      allowNull: true
    },
    {
      name: "read_1_error_rate",
      type: "float",
      allowNull: true
    },
    {
      name: "read_1_first_cycle_int",
      type: "float",
      allowNull: true
    },
    {
      name: "read_1_perc_aligned",
      type: "float",
      allowNull: true
    } 
  ]
});
