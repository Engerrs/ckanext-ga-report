import logging
import datetime

from ckan.lib.cli import CkanCommand
# No other CKAN imports allowed until _load_config is run,
# or logging is disabled


class InitDB(CkanCommand):
    """Initialise the extension's database tables
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        self._load_config()

        import ckan.model as model
        model.Session.remove()
        model.Session.configure(bind=model.meta.engine)
        log = logging.getLogger('ckanext.ga-report')

        import ga_model
        ga_model.init_tables()
        log.info("DB tables are setup")


class GetAuthToken(CkanCommand):
    """ Get's the Google auth token

    Usage: paster getauthtoken <credentials_file>

    Where <credentials_file> is the file name containing the details
    for the service (obtained from https://code.google.com/apis/console).
    By default this is set to credentials.json
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        """
        In this case we don't want a valid service, but rather just to
        force the user through the auth flow. We allow this to complete to
        act as a form of verification instead of just getting the token and
        assuming it is correct.
        """
        from ga_auth import init_service
        init_service('token.dat',
                      self.args[0] if self.args
                                   else 'credentials.json')


class LoadAnalytics(CkanCommand):
    """Get data from Google Analytics API and save it
    in the ga_model

    Usage: paster loadanalytics <tokenfile> <time-period>

    Where <tokenfile> is the name of the auth token file from
    the getauthtoken step.

    And where <time-period> is:
        all         - data for all time
        latest      - (default) just the 'latest' data
        YYYY-MM-DD  - just data for all time periods going
                      back to (and including) this date
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 1

    def command(self):
        self._load_config()

        from download_analytics import DownloadAnalytics
        from ga_auth import (init_service, get_profile_id)

        try:
            svc = init_service(self.args[0], None)
        except TypeError:
            print ('Have you correctly run the getauthtoken task and '
                   'specified the correct file here')
            return

        downloader = DownloadAnalytics(svc, profile_id=get_profile_id(svc))

        time_period = self.args[1] if self.args and len(self.args) > 1 \
            else 'latest'
        if time_period == 'all':
            downloader.all_()
        elif time_period == 'latest':
            downloader.latest()
        else:
            since_date = datetime.datetime.strptime(time_period, '%Y-%m-%d')
            downloader.since_date(since_date)
