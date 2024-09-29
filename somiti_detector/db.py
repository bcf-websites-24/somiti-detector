import psycopg
import dotenv
import os
from psycopg_pool import ConnectionPool

dotenv.load_dotenv(".env")


pool = ConnectionPool(
    f"{os.getenv('DB_CONN_STRING')}",
    min_size=4,
    max_size=24,
    num_workers=24,
)

with pool.connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute("SET TIMEZONE TO 'Asia/Dhaka'")


class User:
    def __init__(self, id, name, roll, batch):
        self.id = str(id)
        self.name = name
        self.roll = roll
        self.batch = int(batch)

    def __str__(self):
        return f"{self.name} ({self.roll})"

    def __repr__(self):
        return f"{self.name} ({self.roll})"


def get_users():
    """
    Get all users
    @return: a list of users
    """
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, student_id, batch FROM users WHERE user_type<>'staff'"
            )
            users = cursor.fetchall()
            users = [User(user[0], user[1], user[2], user[3])
                     for user in users]
            return users


submissions_dict = {}


def get_correct_submissions(user):
    """
    Get the time of correct submissions for a user
    @param user_id: the user id
    @return: a list of datetime objects, indexed by puzzle level - 1
    """

    if user.id in submissions_dict:
        return submissions_dict[user.id]

    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT puzzle_level, submitted_at FROM puzzle_attempts WHERE user_id = %s AND is_correct=true",
                (user.id,),
            )

            submissions = cursor.fetchall()
            # sort by puzzle level
            submissions = sorted(submissions, key=lambda x: x[0])
            # assert that the levels are consecutive
            try:
                if len(submissions) > 0:
                    assert submissions[0][0] == 1
                    for i in range(1, len(submissions)):
                        assert submissions[i][0] == submissions[i - 1][0] + 1
            except AssertionError:
                return []

            # only keep the time
            submissions = [submission[1] for submission in submissions]
            # cache for later
            submissions_dict[user.id] = submissions

            return submissions


def update_user_somiti_score(u, score):
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET shomobay_score = %s WHERE id = %s",
                (score, u.id),
            )


def max_somiti_weight():
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(weight) FROM somiti_graph")
            return cursor.fetchone()[0]
