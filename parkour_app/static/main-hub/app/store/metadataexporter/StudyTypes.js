Ext.define('MainHub.store.metadataexporter.StudyTypes', {
  extend: 'Ext.data.Store',
  storeId: 'ENAStudyTypes',

  fields: [
    {
      name: 'name',
      type: 'string'
    },
    {
      name: 'description',
      type: 'string'
    }
  ],

  data: [
    {
      name: 'Whole Genome Sequencing',
      description: 'Sequencing of a single organism'
    },
    {
      name: 'Metagenomics',
      description: 'Sequencing of a community'
    },
    {
      name: 'Transcriptome Analysis',
      description: 'Sequencing and characterization of transcription elements'
    },
    {
      name: 'Resequencing',
      description: 'Sequencing of a sample with respect to a reference'
    },
    {
      name: 'Epigenetics',
      description: 'Cellular differentiation study'
    },
    {
      name: 'Synthetic Genomics',
      description: 'Sequencing of modified, synthetic, or transplanted genomes'
    },
    {
      name: 'Forensic or Paleo-genomics',
      description: 'Sequencing of recovered genomic material'
    },
    {
      name: 'Gene Regulation Study',
      description: 'Study of gene expression regulation'
    },
    {
      name: 'Cancer Genomics',
      description: 'Study of cancer genomics'
    },
    {
      name: 'Population Genomics',
      description: 'Study of populations and evolution through genomics'
    },
    {
      name: 'RNASeq',
      description: 'RNA sequencing study'
    },
    {
      name: 'Exome Sequencing',
      description: 'The study investigates the exons of the genome'
    },
    {
      name: 'Pooled Clone Sequencing',
      description: 'The study is sequencing clone pools (BACs, fosmids, other constructs)'
    },
    {
      name: 'Transcriptome Sequencing',
      description: 'Sequencing of transcription elements'
    },
    {
      name: 'Other',
      description: 'Study type not listed'
    }
  ]
});
