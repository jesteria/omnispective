from django.conf import settings
from django.core.management import call_command


def main():
    settings.configure(
        TEST_RUNNER='base.NoDbNoseTestSuiteRunner',
    )
    call_command('test')


if __name__ == '__main__':
    main()
