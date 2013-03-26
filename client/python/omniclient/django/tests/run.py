from django.conf import settings
from django.core.management import ManagementUtility


def main():
    settings.configure(
        TEST_RUNNER='base.NoDbNoseTestSuiteRunner',
        INSTALLED_APPS=('django_nose',),
    )
    ManagementUtility().execute()


if __name__ == '__main__':
    main()
