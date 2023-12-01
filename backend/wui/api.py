from common.views import CostUnitsViewSet, DutyViewSet
from flowcell.views import (
    FlowcellAnalysisViewSet,
    FlowcellViewSet,
    PoolViewSet,
    SequencerViewSet,
)
from incoming_libraries.views import IncomingLibrariesViewSet
from index_generator.views import (
    GeneratorIndexTypeViewSet,
    IndexGeneratorViewSet,
    PoolSizeViewSet,
)
from invoicing.views import (
    FixedCostsViewSet,
    InvoicingViewSet,
    LibraryPreparationCostsViewSet,
    SequencingCostsViewSet,
)
from library.views import LibrarySampleTree, LibraryViewSet
from library_preparation.views import LibraryPreparationViewSet
from library_sample_shared.views import (
    ConcentrationMethodViewSet,
    IndexTypeViewSet,
    IndexViewSet,
    LibraryProtocolInvoicingViewSet,
    LibraryProtocolViewSet,
    LibraryTypeViewSet,
    OrganismViewSet,
    ReadLengthInvoicingViewSet,
    ReadLengthViewSet,
)
from metadata_exporter.views import MetadataExporterViewSet
from pooling.views import PoolingViewSet
from request.views import ApproveViewSet, RequestViewSet
from rest_framework import routers
from sample.views import NucleicAcidTypeViewSet, SampleViewSet
from stats.views import RunStatisticsViewSet, SequencesStatisticsViewSet

router = routers.DefaultRouter()

router.register(r"duties", DutyViewSet, basename="duties")
router.register(r"requests", RequestViewSet, basename="request")
router.register(r"approve", ApproveViewSet, basename="approve")
router.register(r"cost_units", CostUnitsViewSet, basename="cost-units")
router.register(r"organisms", OrganismViewSet, basename="organism")
router.register(r"read_lengths", ReadLengthViewSet, basename="read-length")
router.register(
    r"concentration_methods",
    ConcentrationMethodViewSet,
    basename="concentration-method",
)
router.register(r"index_types", IndexTypeViewSet, basename="index-type")
router.register(
    r"generator_index_types", GeneratorIndexTypeViewSet, basename="generator-index-type"
)
router.register(r"indices", IndexViewSet, basename="index")
router.register(
    r"library_protocols", LibraryProtocolViewSet, basename="library-protocol"
)
router.register(
    r"library_protocols_invoicing",
    LibraryProtocolInvoicingViewSet,
    basename="library-protocol-invoicing",
)
router.register(
    r"read_lengths_invoicing",
    ReadLengthInvoicingViewSet,
    basename="read-lengths-invoicing",
)
router.register(r"library_types", LibraryTypeViewSet, basename="library-type")
router.register(
    r"nucleic_acid_types", NucleicAcidTypeViewSet, basename="nucleic-acid-type"
)
router.register(r"pool_sizes", PoolSizeViewSet, basename="pool-size")

router.register(
    r"libraries_and_samples", LibrarySampleTree, basename="libraries-and-samples"
)
router.register(r"libraries", LibraryViewSet, basename="libraries")
router.register(r"samples", SampleViewSet, basename="samples")

router.register(
    r"incoming_libraries", IncomingLibrariesViewSet, basename="incoming-libraries"
)

router.register(r"index_generator", IndexGeneratorViewSet, basename="index-generator")

router.register(
    r"library_preparation", LibraryPreparationViewSet, basename="library-preparation"
)

router.register(r"pooling", PoolingViewSet, basename="pooling")

router.register(r"sequencers", SequencerViewSet, basename="sequencers")
router.register(r"flowcells", FlowcellViewSet, basename="flowcells")
router.register(r"pools", PoolViewSet, basename="pools")

router.register(r"invoicing", InvoicingViewSet, basename="invoicing")
router.register(r"fixed_costs", FixedCostsViewSet, basename="fixed-costs")
router.register(
    r"library_preparation_costs",
    LibraryPreparationCostsViewSet,
    basename="library-preparation-costs",
)
router.register(
    r"sequencing_costs", SequencingCostsViewSet, basename="sequencing-costs"
)

router.register(r"run_statistics", RunStatisticsViewSet, basename="run-statistics")
router.register(
    r"sequences_statistics", SequencesStatisticsViewSet, basename="sequences-statistics"
)
router.register(r"analysis_list", FlowcellAnalysisViewSet, basename="analysis_list")

router.register(
    r"metadata_exporter", MetadataExporterViewSet, basename="metadata_exporter"
)
