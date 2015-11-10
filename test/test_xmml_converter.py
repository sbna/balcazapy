#!/usr/bin/env python
# -*- coding: ascii -*-

"""
Collection of unit tests for the xMMLtoT2Flow converter

"""

__author__ = 'Simone Bna (simone.bna@cineca.it)'
__copyright__ = ''
__license__ = ''
__vcs_id__ = ''
__version__ = ''


import sys
import filecmp
import xmltodict
sys.path.append('../python/balcaza/')
sys.path.append('../python')
import T2FlowBuilderWithCode
import unittest, datetime

## Unittests for the 
class TestxMMLtoT2FlowConverter(unittest.TestCase):

    # test the conversion from xMML to t2flow for a set of test inputs
    def test_conversion(self):
        try:
            outputfilename = "/home/adminuser/Software/balcazapy/test/test_result/xmml/hello_world_2.t2flow"
            sourcefilename = "/home/adminuser/Software/balcazapy/test/test_data/xmml/hello_world_2.xml"
            target_name = "hello_world_2_generated"

            # generate the t2flow by conversion
            targetfilename = target_name + '.t2flow'
            t2flow = open(targetfilename, 'w')
            builder = T2FlowBuilderWithCode.T2FlowFromXMMLBuilder()
            builder.convert(sourcefilename, t2flow, 'flow', False, False, False)
            t2flow.close()

            # we need to set the id of the generated file equal to the id of the test input
            # since this changes every time we run the example
            outputfile = open(outputfilename, 'r')
            parsedoutputfile = xmltodict.parse(outputfile)
            id = parsedoutputfile['workflow']['dataflow']['@id']
            t2flow = open(targetfilename, 'r+')
            t2flow.seek(96, 0)
            t2flow.write(id)
            t2flow.close()

            #check if the file generated is equal to the test data
            self.assertTrue(filecmp.cmp(outputfilename, targetfilename))
        except Exception as e:
            raise Exception(e.message)


print "This is a test on the xMMLtoT2Flow converter"
print "The test starts at " + datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
print ""

suite = unittest.TestLoader().loadTestsFromTestCase(TestxMMLtoT2FlowConverter)
unittest.TextTestRunner(verbosity=2).run(suite)