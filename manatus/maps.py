"""
Maps define how data exposed through `manatus.Scenarios` are manipulated to build `manatus.SourceResource` objects

`manatus.cli.transform` read the configuration file `manatus_scenarios.cfg` to determine which map to apply for which data source
"""
import logging

from manatus.source_resource import SourceResource

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def dc_standard_map(record):
    logger.debug(f'Loaded {__name__}.dc_standard_map map')
    sr = SourceResource()
    if record.contributor:
        sr.contributor = [{'name': name} for name in record.contributor]
    sr.creator = [{'name': name} for name in record.creator if record.creator]
    sr.date = record.date
    sr.description = record.description
    sr.format = record.format
    sr.identifier = record.harvest_id
    sr.language = record.language
    if record.place:
        sr.spatial = [{'name': place} for place in record.place]
    sr.publisher = record.publisher
    sr.rights = record.rights
    if record.subject:
        sr.subject = [{'name': subject} for subject in record.subject]
    sr.title = record.title
    sr.type = record.type
    tn = None
    yield sr, tn


def qdc_standard_map(record):
    logger.debug(f'Loaded {__name__}.qdc_standard_map map')
    for dc_rec, _ in dc_standard_map(record):
        sr = dc_rec
    sr.alternative = record.alternative
    sr.abstract = record.abstract
    sr.collection = record.is_part_of
    sr.extent = record.extent
    tn = None
    yield sr, tn


def mods_standard_map(record):
    logger.debug(f'Loaded {__name__}.mods_standard_map map')
    sr = SourceResource()
    sr.alternative = record.alternative
    try:
        sr.collection = record.collection.title
    except AttributeError:
        logger.info(f"No collection title - {record.harvest_id}")
        pass
    sr.contributor = record.contributor
    sr.creator = record.creator
    sr.date = record.date
    sr.description = record.description
    sr.extent = record.extent
    sr.format = record.format
    sr.identifier = record.harvest_id
    sr.language = record.language
    sr.spatial = record.place
    sr.publisher = record.publisher
    sr.rights = record.rights
    sr.subject = record.subject
    sr.title = record.title
    sr.type = record.type
    tn = None
    yield sr, tn



def marc_standard_map(record):
    """
    Standard MARCXML → DPLA MAPv4 transformation.

    Expects a MARCXMLRecord instance exposing normalized properties.
    Returns a SourceResource and optional thumbnail (None).
    """
    logger.debug(f"Loaded {__name__}.marc_standard_map map")

    sr = SourceResource()
    tn = None

    # --- identifier ---
    try:
        sr.identifier = record.harvest_id
    except AttributeError:
        logger.warning("No harvest_id present on MARCXMLRecord")

    # --- title ---
    if record.title:
        sr.title = record.title

    # --- subject ---
    if record.subject:
        # record.subject is already normalized to MAP-ish dicts
        sr.subject = record.subject

    # --- rights ---
    if record.rights:
        if isinstance(record.rights, str):
            if record.rights.startswith("http"):
                sr.rights = [{"@id": record.rights}]
            else:
                sr.rights = [{"text": record.rights}]
        else:
            # defensive fallback
            sr.rights = record.rights

    # --- type ---
    if record.type:
        sr.type = record.type

    # --- creator / contributor ---
    # Not implemented by default for MARC standard map.
    # Prefer custom maps for institution-specific relator logic.
    #
    # if record.creator:
    #     sr.creator = record.creator
    # if record.contributor:
    #     sr.contributor = record.contributor

    yield sr, tn
