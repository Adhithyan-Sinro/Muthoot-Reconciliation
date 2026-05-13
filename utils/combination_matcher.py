from itertools import combinations


def _scaled_amount(amount):
    return int(round(float(amount) * 100))


def _matching_pair(candidate_indices, candidate_amounts, target_amount, tolerance):
    positions_by_amount = {}

    for position, idx in enumerate(candidate_indices):
        amount_key = _scaled_amount(candidate_amounts[idx])
        positions_by_amount.setdefault(amount_key, []).append(position)

    tolerance_key = max(0, _scaled_amount(tolerance))

    for left_position, left_idx in enumerate(candidate_indices[:-1]):
        needed = float(target_amount) - float(candidate_amounts[left_idx])
        needed_key = _scaled_amount(needed)
        best_right_position = None

        for amount_key in range(
            needed_key - tolerance_key,
            needed_key + tolerance_key + 1
        ):
            for right_position in positions_by_amount.get(amount_key, []):
                if right_position <= left_position:
                    continue

                right_idx = candidate_indices[right_position]
                combo_sum = (
                    float(candidate_amounts[left_idx])
                    + float(candidate_amounts[right_idx])
                )

                if abs(combo_sum - target_amount) <= tolerance:
                    if (
                        best_right_position is None
                        or right_position < best_right_position
                    ):
                        best_right_position = right_position

        if best_right_position is not None:
            return (
                left_idx,
                candidate_indices[best_right_position]
            )

    return None


def _matching_triple(candidate_indices, candidate_amounts, target_amount, tolerance):
    positions_by_amount = {}

    for position, idx in enumerate(candidate_indices):
        amount_key = _scaled_amount(candidate_amounts[idx])
        positions_by_amount.setdefault(amount_key, []).append(position)

    tolerance_key = max(0, _scaled_amount(tolerance))
    last_pair_start = len(candidate_indices) - 2

    for first_position in range(last_pair_start):
        first_idx = candidate_indices[first_position]
        first_amount = float(candidate_amounts[first_idx])

        for second_position in range(first_position + 1, len(candidate_indices) - 1):
            second_idx = candidate_indices[second_position]
            needed = (
                float(target_amount)
                - first_amount
                - float(candidate_amounts[second_idx])
            )
            needed_key = _scaled_amount(needed)
            best_third_position = None

            for amount_key in range(
                needed_key - tolerance_key,
                needed_key + tolerance_key + 1
            ):
                for third_position in positions_by_amount.get(amount_key, []):
                    if third_position <= second_position:
                        continue

                    third_idx = candidate_indices[third_position]
                    combo_sum = (
                        first_amount
                        + float(candidate_amounts[second_idx])
                        + float(candidate_amounts[third_idx])
                    )

                    if abs(combo_sum - target_amount) <= tolerance:
                        if (
                            best_third_position is None
                            or third_position < best_third_position
                        ):
                            best_third_position = third_position

            if best_third_position is not None:
                return (
                    first_idx,
                    second_idx,
                    candidate_indices[best_third_position]
                )

    return None


def find_matching_combinations(
    candidate_indices,
    candidate_amounts,
    target_amount,
    max_combination_size=3,
    tolerance=0.01
):

    """
    Find combinations whose sum matches target amount.

    Parameters
    ----------
    candidate_indices : list
        Transaction indices

    candidate_amounts : dict
        {index: amount}

    target_amount : float

    max_combination_size : int

    tolerance : float

    Returns
    -------
    matched_combo : tuple/list
        Matching indices

    None
    """

    if max_combination_size >= 2:
        matched_pair = _matching_pair(
            candidate_indices,
            candidate_amounts,
            target_amount,
            tolerance
        )

        if matched_pair:
            return matched_pair

    if max_combination_size >= 3:
        matched_triple = _matching_triple(
            candidate_indices,
            candidate_amounts,
            target_amount,
            tolerance
        )

        if matched_triple:
            return matched_triple

    for split_size in range(4, max_combination_size + 1):

        for combo in combinations(candidate_indices, split_size):

            combo_sum = sum(
                candidate_amounts[idx]
                for idx in combo
            )

            if abs(combo_sum - target_amount) <= tolerance:

                return combo

    return None
