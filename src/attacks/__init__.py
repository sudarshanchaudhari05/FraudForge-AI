"""Attack intelligence, genome, mutator, and discovery modules."""

from src.attacks.attack_library import AttackArchetype, AttackLibrary, ATTACK_CATALOG, get_default_attack_library
from src.attacks.attack_mutator import AttackMutator
from src.attacks.attack_genome import AttackGenome, GENOME_VOCABULARY, get_archetype_genome, get_all_known_genomes
from src.attacks.novelty_engine import (
    check_compatibility,
    calculate_genome_similarity,
    calculate_novelty_score,
    calculate_realism_score,
    calculate_evasion_potential,
    calculate_priority_score,
    generate_candidate_name,
)
from src.attacks.attack_discovery import AttackDiscoveryEngine, NovelAttackCandidate
