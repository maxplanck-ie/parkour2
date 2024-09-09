import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from explorer.models import Query


class Command(BaseCommand):
    help = "Creates sample queries for django-sql-explorer."

    def handle(self, *args, **options):
        assert settings.DEBUG
        try:
            queries = Query.objects.all().count()
            if queries == 0:
                confident_reads1 = Query(
                    sql="""SELECT fc.flowcell_id,
                                  fc.create_time as flowcell_time,
                                  x.*
                           FROM flowcell_flowcell fc,
                                jsonb_to_recordset(fc.sequences)
                                as x(
                                    barcode text,
                                    confident_reads float
                                )
                            ;""",
                    title="Confident Reads v1",
                )
                confident_reads1.save()

                confident_reads2 = Query(
                    sql="""SELECT fc.flowcell_id,
                                  fc.create_time as flowcell_time,
                                  x.*,
                                  sam.name as sample_name,
                                  (sam.sequencing_depth*1e6) as requested_depth,
                                  org.name as organism,
                                  lib_prep.starting_amount as starting_amount,
                                  lib_prep.pcr_cycles as pcr_cycles,
                                  lib_prep.concentration_library as concentration_library,
                                  lib_prep.mean_fragment_size as mean_fragment_size,
                                  R.name as request_name,
                                  R.create_time as request_time,
                                  Lt.name as library_type,
                                  Lp.name as library_protocol
                            FROM flowcell_flowcell fc,
                                 jsonb_to_recordset(fc.sequences)
                                 as x(
                                   barcode text,
                                   confident_reads float,
                                   reads_pf_sequenced float
                                 ),
                                 sample_sample sam,
                                 library_sample_shared_librarytype Lt,
                                 library_sample_shared_libraryprotocol Lp,
                                 library_sample_shared_organism org,
                                 request_request R,
                                 request_request_samples Rs,
                                 library_preparation_librarypreparation lib_prep
                            WHERE sam.barcode = x.barcode
                            AND sam.library_type_id = Lt.id
                            AND sam.library_protocol_id = Lp.id
                            AND sam.organism_id = org.id
                            AND Rs.sample_id = sam.id
                            AND Rs.request_id = R.id
                            AND lib_prep.sample_id = sam.id
                            ;""",
                    title="Confident Reads v2",
                )
                confident_reads2.save()

                read_stats = Query(
                    sql="""SELECT fc.flowcell_id,
                          fc.create_time as flowcell_time,
                          x.*,
                          sam.name as sample_name,
                          (sam.sequencing_depth*1e6) as requested_depth,
                          org.name as organism,
                          lib_prep.starting_amount as starting_amount,
                          lib_prep.pcr_cycles as pcr_cycles,
                          lib_prep.concentration_library as concentration_library,
                          lib_prep.mean_fragment_size as mean_fragment_size,
                          R.name as request_name,
                          R.create_time as request_time,
                          Lt.name as library_type,
                          Lp.name as library_protocol
                        /* some fields are read as text to avoid failure on empty fields "" */
                        FROM flowcell_flowcell fc,
                             jsonb_to_recordset(fc.sequences)
                             as x(
                               barcode text,
                               confident_reads float,
                               reads_pf_sequenced float,
                               optical_duplicates text,
                               mapped_reads text,
                               insert_size text,
                               dupped_reads text,
                               /*
                               uniq_mapped float,
                               multi_mapped float,
                               assigned_reads float,
                               */
                               "rRNA_rate" float
                             ),
                             sample_sample sam,
                             library_sample_shared_librarytype Lt,
                             library_sample_shared_libraryprotocol Lp,
                             library_sample_shared_organism org,
                             request_request R,
                             request_request_samples Rs,
                             library_preparation_librarypreparation lib_prep
                        WHERE sam.barcode = x.barcode
                        AND sam.library_type_id = Lt.id
                        AND sam.library_protocol_id = Lp.id
                        AND sam.organism_id = org.id
                        AND Rs.sample_id = sam.id
                        AND Rs.request_id = R.id
                        AND lib_prep.sample_id = sam.id
                        ;""",
                    title="read_stats",
                )
                read_stats.save()
            self.stdout.write(self.style.SUCCESS("Successfully created sample queries"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
