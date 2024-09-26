import math

eps = 1e-7


def log_normal(x, mu, sigma):
    """
    Log-normal distribution
    @param x: the value
    @param mu: the mean
    @param sigma: the standard deviation
    @return: the log probability at x
    """
    x = max(x, eps)
    return -(((math.log(x) - math.log(mu)) / math.log(sigma)) ** 2)
