import math
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from .config import config
from .dist import log_normal
from .db import pool, get_correct_submissions


def temporal_score(dt):
    """
    Calculate a score based on the time difference
    @param dt: the time difference
    @return: the score
    """
    if config.dt_dist == "log_normal":
        return log_normal(dt, config.dt_avg, config.dt_std)
    else:
        raise ValueError(f"Unknown distribution: {config.dt_dist}")


def total_temporal_score(sub1, sub2):

    N = min(len(sub1), len(sub2))
    score = 0.0
    for i in range(N):
        score += temporal_score(abs((sub1[i] - sub2[i]).total_seconds()))

    score /= N
    score = math.pow(math.e, score)

    return score


def overlap_score(sub1, sub2):
    """
    Calculate a score based on the time spent on the same puzzle level relative to the total time spent
    @param dt: the time difference
    @return: the score
    """

    skip_levels = [30, 61, 81]

    total_time = 0
    overlap_time = 0
    total_time = max(
        (sub1[-1] - sub1[0]).total_seconds(), (sub2[-1] - sub2[0]).total_seconds()
    )
    for i in range(1, min(len(sub1), len(sub2))):
        if i in skip_levels:
            continue

        overlap_time += max(
            (min(sub1[i], sub2[i]) - max(sub1[i - 1], sub2[i - 1])).total_seconds(), 0
        )
    return overlap_time / total_time


def edge_score(u1, u2, sub1, sub2):
    # 15 puzzle grace period
    if min(len(sub1), len(sub2)) < 15:
        return 0.0

    return (
        config.temporal_weight * total_temporal_score(sub1, sub2)
        + config.overlap_weight * overlap_score(sub1, sub2)
        + config.batch_diff_weight
        * config.batch_diff_multiplier ** (-abs(u1.batch - u2.batch))
    )


def calc_user_edge_scores(user, users):
    sub1 = get_correct_submissions(user)
    somiti_scores = []

    for other_user in tqdm(users):
        score = 0.0
        if other_user.id == user.id:
            continue

        sub2 = get_correct_submissions(other_user)
        score = edge_score(user, other_user, sub1, sub2)

        somiti_scores.append((score, other_user))

    somiti_scores.sort(reverse=True, key=lambda x: x[0])
    return somiti_scores


def calc_score(u1, u2):
    sub1 = get_correct_submissions(u1)
    sub2 = get_correct_submissions(u2)
    score = edge_score(u1, u2, sub1, sub2)
    return (u1, u2, score)


def update_score(entries):
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            query = """
                INSERT INTO somiti_graph (user_id1, user_id2, weight)
                VALUES (%s, %s, %s)
            """

            data = [(u1.id, u2.id, score) for u1, u2, score in entries]
            cursor.executemany(query, data)


def calc_edge_scores(users):
    tasks = []
    entries = []

    with ThreadPoolExecutor(max_workers=24) as executor:
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                tasks.append(executor.submit(calc_score, users[i], users[j]))

        for task in tqdm(tasks):
            entries.append(task.result())

    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM somiti_graph")

    workers = 24
    tasks = []
    batch = 100
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(0, len(entries), batch):
            tasks.append(
                executor.submit(
                    update_score,
                    entries[i : min(i + batch, len(entries))],
                )
            )

        for task in tqdm(tasks):
            task.result()


def cal_edge_scores_local(users):
    tasks = []
    entries = []

    with ThreadPoolExecutor(max_workers=24) as executor:
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                tasks.append(executor.submit(calc_score, users[i], users[j]))

        for task in tqdm(tasks):
            entries.append(task.result())

    return entries
