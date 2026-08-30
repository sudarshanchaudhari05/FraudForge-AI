"""Unit tests for Attack Genome Engine and Schema."""

import pytest
from src.attacks.attack_genome import (
    AttackGenome,
    GENOME_VOCABULARY,
    GENE_KEYS,
    KNOWN_ATTACK_GENOMES,
    get_archetype_genome,
    get_all_known_genomes,
)
from src.attacks.attack_library import ATTACK_CATALOG


def test_all_28_archetypes_mapped():
    """Verify all 28 existing attack archetypes have ground-truth genome mappings."""
    assert len(KNOWN_ATTACK_GENOMES) == 28
    assert len(KNOWN_ATTACK_GENOMES) == len(ATTACK_CATALOG)

    for archetype in ATTACK_CATALOG:
        genome = get_archetype_genome(archetype.attack_id)
        assert genome is not None, f"Missing genome mapping for {archetype.attack_id}"
        assert genome.attack_id == archetype.attack_id
        assert genome.category == archetype.category


def test_genome_gene_vocabulary_validity():
    """Verify every gene in every mapped genome belongs to the defined vocabulary."""
    for atk_id, genome in KNOWN_ATTACK_GENOMES.items():
        genes = genome.get_genes()
        assert len(genes) == 10
        for gene_key, gene_val in genes.items():
            assert gene_key in GENOME_VOCABULARY
            assert gene_val in GENOME_VOCABULARY[gene_key], (
                f"Invalid value '{gene_val}' for gene '{gene_key}' in {atk_id}"
            )


def test_genome_serialization_roundtrip():
    """Test dictionary serialization and deserialization."""
    genome = get_archetype_genome("ATK-001")
    assert genome is not None

    d = genome.to_dict()
    assert isinstance(d, dict)
    assert d["attack_id"] == "ATK-001"
    assert d["target"] == "payment_authorization"

    restored = AttackGenome.from_dict(d)
    assert restored.attack_id == genome.attack_id
    assert restored.get_genes() == genome.get_genes()


def test_to_simulation_parameters_generation():
    """Verify conversion from AttackGenome into concrete simulation parameters."""
    genome = get_archetype_genome("ATK-013")  # Low-and-Slow AI Micro-Carding Swarm
    assert genome is not None

    params = genome.to_simulation_parameters()
    assert isinstance(params, dict)
    assert params["payment_channel"] == "e-commerce"
    assert "fixed_amount_range" in params
    assert params["fixed_amount_range"][0] <= params["fixed_amount_range"][1]
    assert "velocity_1h_boost" in params


def test_get_all_known_genomes_list():
    """Verify helper returns complete list of genomes."""
    all_genomes = get_all_known_genomes()
    assert len(all_genomes) == 28
    assert all(isinstance(g, AttackGenome) for g in all_genomes)
