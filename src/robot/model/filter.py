#  Copyright 2008-2014 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from robot.utils import setter

from .tags import TagPatterns
from .namepatterns import SuiteNamePatterns, TestNamePatterns
from .visitor import SuiteVisitor
import requests
import os

class EmptySuiteRemover(SuiteVisitor):

    def end_suite(self, suite):
        suite.suites = [s for s in suite.suites if s.test_count]

    def visit_test(self, test):
        pass

    def visit_keyword(self, kw):
        pass


class Filter(EmptySuiteRemover):

    def __init__(self, include_suites=None, include_tests=None,
                 include_tags=None, exclude_tags=None, runnerExtension=None):
        self.include_suites = include_suites
        self.include_tests = include_tests
        self.include_tags = include_tags
        self.exclude_tags = exclude_tags
        self.runnerExtension = runnerExtension

    @setter
    def include_suites(self, suites):
        return SuiteNamePatterns(suites) \
            if not isinstance(suites, SuiteNamePatterns) else suites

    @setter
    def include_tests(self, tests):
        return TestNamePatterns(tests) \
            if not isinstance(tests, TestNamePatterns) else tests

    @setter
    def include_tags(self, tags):
        return TagPatterns(tags) if not isinstance(tags, TagPatterns) else tags

    @setter
    def exclude_tags(self, tags):
        return TagPatterns(tags) if not isinstance(tags, TagPatterns) else tags

    def start_suite(self, suite):
        if not self:
            return False
        if hasattr(suite, 'starttime'):
            suite.starttime = suite.endtime = None
        if self.include_suites:
            return self._filter_by_suite_name(suite)
        if self.include_tests:
            suite.tests = self._filter(suite, self._included_by_test_name)
        if self.include_tags:
            suite.tests = self._filter(suite, self._included_by_tags)
            if self.runnerExtension is not None:
                """
                When the runner exists, it filters all the tests again
                based on the available liceses and the test tags
                """
                suite.tests = self.filterTestsBasedOnLicenses(suite.tests)
        if self.exclude_tags:
            suite.tests = self._filter(suite, self._not_excluded_by_tags)
        return bool(suite.suites)

    def filterTestsBasedOnLicenses(self, tests):
        """
        Based on the filtered tests, this method will check with the
        runner extension if the test case can or not be executed
        according to its license tags.
        """
        filteredTests = []
        for i in range(len(tests)):
            test = tests[i]
            testName = test.name
            testSuite = test.parent._name
            soiVersion=""
            
            if self.runnerExtension.shouldTestBeExecuted(test.name, test.tags):
                if(os.environ.get('BSCS_PROJECT') is not None and os.environ['BSCS_PROJECT'] == "BSCS17"):
                    url = 'http://localhost:8080/getTestcaseCoreLoopStage'
                    if(os.environ.get('ONEDCLMONITOR_SERVER') is not None):
                        url = 'http://'+os.environ['ONEDCLMONITOR_SERVER']+'/getTestcaseCoreLoopStage'
                        
                    soiVersion = self.runnerExtension.getSoiVersion()
                    url = url+'?name='+test.name+'&suite='+testSuite+'&project='+os.environ['BSCS_PROJECT']+'&soiVersion='+soiVersion
                    headers = {"Content-type": "application/json", "Accept":"application/json"}
                    response = requests.get(url, headers=headers)
                    testcaseStage = response.text[1:-1]
                    
                    if(testcaseStage == "ALL" and os.environ['TESTCASE_STAGE'] == "STAGING"):
                        """
                        It means that the test case is new in the database and the current loop is STAGING.
                        So we have to include the test to be executed
                        """
                        filteredTests.append(test)
                        
                    elif (os.environ['TESTCASE_STAGE'] == testcaseStage): 
                        filteredTests.append(test)
                else:
                    filteredTests.append(test)
                    
        return filteredTests

    def _filter_by_suite_name(self, suite):
        if self.include_suites.match(suite.name, suite.longname):
            suite.visit(Filter(include_suites=[],
                               include_tests=self.include_tests,
                               include_tags=self.include_tags,
                               exclude_tags=self.exclude_tags,
                               runnerExtension=self.runnerExtension))
            return False
        suite.tests = []
        return True

    def _filter(self, suite, filter):
        return [t for t in suite.tests if filter(t)]

    def _included_by_test_name(self, test):
        return self.include_tests.match(test.name, test.longname)

    def _included_by_tags(self, test):
        return self.include_tags.match(test.tags)

    def _not_excluded_by_tags(self, test):
        return not self.exclude_tags.match(test.tags)

    def __nonzero__(self):
        return bool(self.include_suites or self.include_tests or
                    self.include_tags or self.exclude_tags)
