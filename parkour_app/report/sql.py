LIBRARY_SELECT = '''
record.mean_fragment_size AS "Mean Fragment Size",
record.qpcr_result AS "qPCR Result",
record.qpcr_result_facility AS "qPCR Result (Facility)"
'''

SAMPLE_SELECT = '''
record.rna_quality AS "RNA Quality",
record.rna_quality_facility AS "RNA Quality (Facility)",
nat.name AS "Nucleic Acid Type",
lprep.starting_amount AS "Starting Amount",
lprep.spike_in_volume AS "Spike-in Volume",
lprep.pcr_cycles AS "PCR Cycles",
lprep.concentration_library AS "Concentration Library",
lprep.mean_fragment_size AS "Mean Fragment Size",
lprep."nM" AS "nM",
lprep.qpcr_result AS "qPCR Result"
'''

SAMPLE_JOINS = '''
LEFT JOIN sample_nucleicacidtype as nat
    ON record.nucleic_acid_type_id = nat.id
LEFT JOIN library_preparation_librarypreparation as lprep
    ON record.id = lprep.sample_id
'''

QUERY = '''
SELECT *
FROM (
    SELECT record.id AS t1_id,
        record.name AS "Name",
        record.barcode AS "Barcode",
        record.status AS "Status",
        record.concentration AS "Concentration",
        record.sequencing_depth AS "Sequencing Depth",
        record.equal_representation_nucleotides AS "Equal Representation of Nucleotides",
        record.index_reads AS "Index Reads",
        record.index_i7 AS "Index I7",
        record.index_i5 AS "Index I5",
        record.amplification_cycles AS "Amplification Cycles",
        record.dilution_factor AS "Dilution Factor",
        record.concentration_facility AS "Concentration (Facility)",
        record.sample_volume_facility AS "Sample Volume (Facility)",
        record.amount_facility AS "Amount (Facility)",
        record.size_distribution_facility AS "Size Distribution (Facility)",

        (
            SELECT concat(i.prefix, i.number)
            FROM library_sample_shared_indextype as it
            INNER JOIN library_sample_shared_indextype_indices_i7 AS indices
                ON it.id = indices.indextype_id
            INNER JOIN library_sample_shared_indexi7 as i
                ON indices.id = i.id
            WHERE it.id = record.index_type_id AND i.index = record.index_i7
            LIMIT 1
        ) AS "Index I7 ID",

        (
            SELECT concat(i.prefix, i.number)
            FROM library_sample_shared_indextype as it
            INNER JOIN library_sample_shared_indextype_indices_i5 AS indices
                ON it.id = indices.indextype_id
            INNER JOIN library_sample_shared_indexi5 as i
                ON indices.id = i.id
            WHERE it.id = record.index_type_id AND i.index = record.index_i5
            LIMIT 1
        ) AS "Index I5 ID",


        r.name AS "Request",
        concat(u.first_name, ' ', u.last_name) AS "User",
        lp.name AS "Library Protocol",
        lt.name AS "Library Type",
        o.name AS "Organism",
        rl.name AS "Read Length",
        cm.name AS "Concentration Method",
        it.name AS "Index Type",
        cmf.name AS "Concentration Method (Facility)",
        pooling.concentration_c1 AS "Concentration C1",
        p.name AS "Pool",
        concat(psize.multiplier, 'x', psize.size) AS "Pool Size",
        

        /* Sample-specific fields */
        {select}

    FROM {table_name}_{table_name} as record

    LEFT JOIN request_request_{table_name_plural} as rs
        ON record.id = rs.{table_name}_id

    LEFT JOIN request_request as r
        ON rs.request_id = r.id

    LEFT JOIN auth_user as u
        ON r.user_id = u.id

    LEFT JOIN library_sample_shared_libraryprotocol as lp
        ON record.library_protocol_id = lp.id

    LEFT JOIN library_sample_shared_librarytype as lt
        ON record.library_type_id = lt.id

    LEFT JOIN library_sample_shared_organism as o
        ON record.organism_id = o.id

    LEFT JOIN library_sample_shared_readlength as rl
        ON record.read_length_id = rl.id

    LEFT JOIN library_sample_shared_concentrationmethod as cm
        ON record.concentration_method_id = cm.id

    LEFT JOIN library_sample_shared_concentrationmethod as cmf
        ON record.concentration_method_facility_id = cmf.id

    LEFT JOIN library_sample_shared_indextype as it
        ON record.index_type_id = it.id

    LEFT JOIN index_generator_pool_{table_name_plural} as ps
        ON record.id = ps.{table_name}_id

    LEFT JOIN index_generator_pool as p
        ON ps.pool_id = p.id

    LEFT JOIN index_generator_poolsize as psize
        ON p.size_id = psize.id

    LEFT JOIN pooling_pooling as pooling
        ON record.id = pooling.{table_name}_id
    
    

    /* Sample-specific joins */
    {joins}
) t1


LEFT JOIN (
    SELECT record.id AS t2_id, f.create_time::date AS "Flowcell create time",
        array_to_string(array_agg(DISTINCT s.name), ', ') AS "Sequencer"
    FROM {table_name}_{table_name} AS record
    LEFT JOIN index_generator_pool_{table_name_plural} as ps
        ON record.id = ps.{table_name}_id
    LEFT JOIN index_generator_pool as p
        ON ps.pool_id = p.id
    LEFT JOIN flowcell_lane as l
        ON p.id = l.pool_id
    LEFT JOIN flowcell_flowcell_lanes as fl
        ON l.id = fl.lane_id
    LEFT JOIN flowcell_flowcell as f
        ON fl.flowcell_id = f.id
    LEFT JOIN flowcell_sequencer AS s
        ON f.sequencer_id = s.id
    GROUP BY record.id, f.create_time::date
) t2 ON t1_id = t2_id
'''
