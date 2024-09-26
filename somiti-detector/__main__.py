import datetime
from .config import Config
from .dist import log_normal
from .db import *
import math
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

config = Config()


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
    total_time = 0
    overlap_time = 0
    total_time = max(
        (sub1[-1] - sub1[0]).total_seconds(), (sub2[-1] - sub2[0]).total_seconds()
    )
    for i in range(1, min(len(sub1), len(sub2))):
        overlap_time += max(
            (min(sub1[i], sub2[i]) - max(sub1[i - 1], sub2[i - 1])).total_seconds(), 0
        )
    return overlap_time / total_time


def somiti_score(u1, u2, sub1, sub2):
    # 10 puzzle grace period
    if min(len(sub1), len(sub2)) < 10:
        return 0.0

    return (
        config.temporal_weight * total_temporal_score(sub1, sub2)
        + config.overlap_weight * overlap_score(sub1, sub2)
        + config.batch_diff_weight * 2 ** (-abs(u1.batch - u2.batch))
    )


def calc_user_somiti_scores(user, users):
    sub1 = get_correct_submissions(user)
    somiti_scores = []

    for other_user in tqdm(users):
        score = 0.0
        if other_user.id == user.id:
            continue

        sub2 = get_correct_submissions(other_user)
        score = somiti_score(user, other_user, sub1, sub2)

        somiti_scores.append((score, other_user))

    somiti_scores.sort(reverse=True, key=lambda x: x[0])
    return somiti_scores


def calc_and_update_somiti_score(u1, u2):
    sub1 = get_correct_submissions(u1)
    sub2 = get_correct_submissions(u2)
    score = somiti_score(u1, u2, sub1, sub2)

    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM somiti_graph WHERE user_id1 = %s AND user_id2 = %s",
                (u1.id, u2.id),
            )
            try:
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO somiti_graph (user_id1, user_id2, weight) VALUES (%s, %s, %s)",
                        (u1.id, u2.id, score),
                    )
                else:
                    cursor.execute(
                        "UPDATE somiti_graph SET weight = %s WHERE user_id1 = %s AND user_id2 = %s",
                        (score, u1.id, u2.id),
                    )
            except Exception as e:
                print(f"Error: {e}")


def calc_all_somiti_scores(users):
    tasks = []

    with ThreadPoolExecutor(max_workers=24) as executor:
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                tasks.append(
                    executor.submit(calc_and_update_somiti_score, users[i], users[j])
                )

        for task in tqdm(tasks):
            task.result()


users = get_users()


# somiti_scores = calc_user_somiti_scores(
#     User("1f96ee34-8729-4307-ad11-5d20ebd52f3f", "AntonyTheGOAT", 2014), users
# )
calc_all_somiti_scores(users)

connection.close()
