"""Catalog and Attack Genome vocabulary routes."""

from typing import List
from fastapi import APIRouter

from src.api.schemas import AttackArchetypeSchema, GenomeVocabularyResponse
from src.attacks.attack_library import get_default_attack_library
from src.attacks.attack_genome import (
    AttackGenome,
    GENOME_VOCABULARY,
    GENE_KEYS,
    get_archetype_genome,
)

GENOME_DESCRIPTIONS = {
    "target": "Target entity of the fraud operation (account, identity, merchant, etc.)",
    "entry_vector": "Primary exploitation vector (credential abuse, deepfake, prompt injection, etc.)",
    "behavior": "Velocity and transaction sequencing pattern",
    "evasion_strategy": "Mechanism used to suppress risk signals and blend with normal traffic",
    "payment_channel": "Payment channel exploited (e-commerce, pos_chip, mobile_app, etc.)",
    "amount_strategy": "Transaction amount structuring pattern",
    "temporal_strategy": "Timing distribution of transactions",
    "identity_strategy": "Type of identity manipulation (synthetic, takeover, authorized victim)",
    "merchant_strategy": "Merchant targeting pattern and category distribution",
    "geographic_strategy": "IP, origin, and geographical routing camouflage",
}

router = APIRouter(prefix="/catalog", tags=["Catalog & Genome"])


@router.get("/known-attacks", response_model=List[AttackArchetypeSchema])
def get_known_attacks() -> List[AttackArchetypeSchema]:
    """Return all 28 known GenAI payment-fraud archetypes with their genome representations."""
    lib = get_default_attack_library()
    archetypes = lib.get_all()
    results = []

    for arch in archetypes:
        genome_obj = get_archetype_genome(arch.attack_id)
        genes_dict = genome_obj.get_genes() if genome_obj else {}
        results.append(
            AttackArchetypeSchema(
                attack_id=arch.attack_id,
                name=arch.name,
                category=arch.category,
                severity=arch.severity,
                payment_channel=arch.affected_payment_surface,
                indicators=arch.behavioral_indicators,
                description=arch.description,
                genome=genes_dict,
            )
        )

    return results


@router.get("/genome-vocabulary", response_model=GenomeVocabularyResponse)
def get_genome_vocabulary() -> GenomeVocabularyResponse:
    """Return the 10-dimensional Attack Genome vocabulary and descriptions."""
    return GenomeVocabularyResponse(
        dimensions=GENE_KEYS,
        vocabulary=GENOME_VOCABULARY,
        descriptions=GENOME_DESCRIPTIONS,
    )
