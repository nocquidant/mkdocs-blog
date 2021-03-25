import datetime
import os.path
import re

from jinja2 import Environment
from mkdocs.plugins import BasePlugin

from . import cleaner, jinja_filters, rss

pattern = ".*(\d{4})/(\d{2})/"

class Blog(BasePlugin):
    def parse_url(self, url):
        try:
            r = re.search(pattern, url)
            if r:
                year = int(r.group(1))
                month = int(r.group(2))
                return (year, month)
            else:
                return None
        except:
            return None

    def on_nav(self, nav, config, files):
        self.nav = nav

        # ordered by time
        ordered = []
        # nested by year and month
        chronological = {}

        for f in files:
            if not f.is_documentation_page():
                continue
            
            # Filter non blog pages
            if not f.page:
                continue
            if not re.match(pattern, str(f.url)) :
                continue

            # Read title
            f.page.read_source(config)

            parsed = self.parse_url(f.url)
            if parsed:
                year, month = parsed

                yeartime = datetime.datetime(year, 1, 1)
                monthtime = datetime.datetime(year, month, 1)
                # file modified time used as tie-breaker
                # since no other intra-month signal is available
                mtime = os.path.getmtime(f.abs_src_path)

                ordered.append((f.page, year, month, mtime))

                if yeartime not in chronological:
                    chronological[yeartime] = {}
                if monthtime not in chronological[yeartime]:
                    chronological[yeartime][monthtime] = {}

                # if we have an mtime collision, we'll just sort
                # by whatever order the nav contains them in
                while mtime in chronological[yeartime][monthtime]:
                    mtime += 1

                chronological[yeartime][monthtime][mtime] = f.page

        ordered.sort(key=lambda tup: (tup[1], tup[2], tup[3]))

        config['ordered'] = ordered
        config['chronological'] = chronological

        rss.generate(nav, config, files)

        return nav

    def on_page_content(self, html, page, config, files):
        env = Environment()
        env.filters['strftime'] = jinja_filters.strftime

        cleaned = cleaner.clean(html)

        return env.from_string(cleaned).render(
            config=config,
            nav=self.nav,
            files=files
        )
