# -*- coding: utf-8 -*-
"""Search module init."""

from agent_eyes.search.exa import search_web
from agent_eyes.search.reddit import search_reddit
from agent_eyes.search.github import search_github, search_github_issues
from agent_eyes.search.twitter import search_twitter, get_user_tweets

__all__ = [
    "search_web",
    "search_reddit",
    "search_github",
    "search_github_issues",
    "search_twitter",
    "get_user_tweets",
]
