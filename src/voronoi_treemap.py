import random


def sample_points(weights: dict, rng: random.Random, total_points: int = 2000) -> dict:
    """Sample points within the unit square [0,1]x[0,1], allocated to each
    group proportional to its weight (largest-remainder method, so counts
    sum to exactly total_points), with every group guaranteed at least 1
    point so it still produces a valid Voronoi cell downstream."""
    groups = list(weights.keys())
    total_weight = sum(weights.values())
    raw_counts = {g: total_points * weights[g] / total_weight for g in groups}
    counts = {g: int(raw_counts[g]) for g in groups}

    remainder = total_points - sum(counts.values())
    by_fractional_part = sorted(
        groups, key=lambda g: raw_counts[g] - counts[g], reverse=True
    )
    for g in by_fractional_part[:remainder]:
        counts[g] += 1

    zero_groups = [g for g in groups if counts[g] == 0]
    for g in zero_groups:
        donor = max(groups, key=lambda h: counts[h])
        counts[donor] -= 1
        counts[g] = 1

    return {
        g: [(rng.random(), rng.random()) for _ in range(counts[g])]
        for g in groups
    }
