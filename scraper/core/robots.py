import re
import urllib.robotparser
from typing import Optional

class RobotsChecker:
    """
    Wrapper around urllib.robotparser to check robots.txt rules for a given user-agent.
    """
    def __init__(self, robots_txt_url: str, user_agent: str = '*'):
        self.robots_txt_url = robots_txt_url
        self.user_agent = user_agent
        self.parser = urllib.robotparser.RobotFileParser()
        self.parser.set_url(robots_txt_url)
        self.parser.read()

    def can_fetch(self, url: str) -> bool:
        """
        Returns True if the user-agent is allowed to fetch the given URL.
        """
        return self.parser.can_fetch(self.user_agent, url)

    def crawl_delay(self) -> Optional[float]:
        """
        Returns the crawl-delay for the user-agent, or None if not specified.
        """
        return self.parser.crawl_delay(self.user_agent)
