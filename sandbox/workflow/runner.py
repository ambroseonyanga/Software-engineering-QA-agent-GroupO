"""Trusted container entry point for one approved test module."""
import json
import os
import sys
import unittest

sys.path[:0] = ['/qa', '/qa/proposals', '/workspace']
mode, module = sys.argv[1:3]


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'name': test.id(), 'status': 'passed', 'detail': ''})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.records.append({'name': test.id(), 'status': 'failed', 'detail': self._exc_info_to_string(error, test)[-6000:]})

    def addError(self, test, error):
        super().addError(test, error)
        self.records.append({'name': test.id(), 'status': 'error', 'detail': self._exc_info_to_string(error, test)[-6000:]})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({'name': test.id(), 'status': 'skipped', 'detail': str(reason)})

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        if error:
            self.records.append({'name': str(subtest), 'status': 'failed' if issubclass(error[0], test.failureException) else 'error',
                                 'detail': self._exc_info_to_string(error, test)[-6000:]})


class Runner(unittest.TextTestRunner):
    resultclass = Result

    def run(self, suite):
        result = super().run(suite)
        Runner.last_result = result
        return result


if mode == 'budgetme':
    os.environ['DJANGO_SETTINGS_MODULE'] = '_qa_settings'
    import django
    django.setup()
    from django.test.runner import DiscoverRunner
    class DjangoRunner(DiscoverRunner):
        test_runner = Runner
    DjangoRunner(verbosity=2, interactive=False).run_tests([module])
    result = Runner.last_result
else:
    suite = unittest.defaultTestLoader.loadTestsFromName(module)
    result = Runner(verbosity=2).run(suite)

statuses = {record['status'] for record in result.records}
if result.testsRun < 1 or result.testsRun > 20 or result.expectedFailures or result.unexpectedSuccesses or not statuses:
    status = 'error'
elif 'error' in statuses:
    status = 'error'
elif 'failed' in statuses:
    status = 'failed'
elif 'skipped' in statuses:
    status = 'skipped'
else:
    status = 'passed'
print('QA_RESULT_JSON=' + json.dumps({'status': status, 'tests_run': result.testsRun, 'records': result.records}))
sys.exit(0 if status in {'passed', 'skipped'} else 1)
