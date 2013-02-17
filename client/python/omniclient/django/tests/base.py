from django_nose import NoseTestSuiteRunner


class NoDbNoseTestSuiteRunner(NoseTestSuiteRunner):

    def setup_databases(self):
        pass

    def teardown_databases(self, *_args):
        pass
