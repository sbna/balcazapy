# Copyright (C) 2013 Cardiff University
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import sys, os
sys.path.append('../../python')
from balcaza.t2types import *
from balcaza.t2activity import *
from balcaza.t2flow import Workflow

def readZapyFile(sourceFile, flowName):
    with open(sourceFile) as f:
        source = f.read()
    code = compile(source, sourceFile, 'exec')
    module = {}
    exec(code, module)
    return module[flowName]


def printSig(sourceFile, flowName):
    import sys
    flow = readZapyFile(sourceFile, flowName)
    sys.stdout.write("NestedZapyFile(\n")
    sys.stdout.write("    '%s',\n" % sourceFile)
    if flow.input:
        sys.stdout.write("    inputs = dict(\n")
        sys.stdout.write(",\n".join(["        %s = %s" % (port.name, port.type) for port in flow.input]))
        sys.stdout.write("\n        ),\n")
    if flow.output:
        sys.stdout.write("    outputs = dict(\n")
        sys.stdout.write(",\n".join(["        %s = %s" % (port.name, port.type) for port in flow.output]))
        sys.stdout.write("\n        )\n")
    sys.stdout.write(")\n")


class Terminal:
  
    def __init__(self, kind=None):
        self.ports = {'out' : {}, 'in' : {}}
        self.kind = kind
    
    def set_type(self, kind):
        self.kind = kind
    
    def add_port(self, port_id, port_value):
        if self.kind == 'source':
            self.ports['out'][port_id] = port_value
        elif self.kind == 'sink':
            self.ports['in'][port_id] = port_value
        else:
            raise Exception('Error: the kind of terminal is not set!')

class Instance:
    def __init__(self, kind, content):
        self.kind = kind
        self.content = content


class T2FlowFromXMMLBuilder:

    def create_terminal(self, x):
        terminal = Terminal(kind=x['@type'])
        if 'out' in x['ports'].keys():
            if type(x['ports']['out']) is list:
                for port in x['ports']['out']:
                    port_id = port['@id']
                    port_value = {'datatype' : port['@datatype']}
                    terminal.add_port(port_id, port_value)
            else:
                port_id = x['ports']['out']['@id']
                port_value = {'datatype' : x['ports']['out']['@datatype']}
                terminal.add_port(port_id, port_value)
        if 'in' in x['ports'].keys():
            if type(x['ports']['in']) is list:
                for port in x['ports']['in']:
                    port_id = port['@id']
                    port_value = {'datatype' : port['@datatype']}
                    terminal.add_port(port_id, port_value)
            else:
                port_id = x['ports']['in']['@id']
                port_value = {'datatype' : x['ports']['in']['@datatype']}
                terminal.add_port(port_id, port_value)
        terminal.add_port
        return terminal

    def create_submodel(self, flow, x):
        implementation_code  = str(x['implementation']['code']['#text'])
        task_name = x['@id']
        if x['@type'] == 'BeanshellCode':
            #loop over in-ports
            myinputs = dict()
            if type(x['ports']['in']) is list:
                for in_ports in x['ports']['in']:
                    if in_ports['@datatype'] == 'string':
                        myinputs[in_ports['@id']] = String
            else:
                if x['ports']['in']['@datatype'] == 'string':
                    myinputs[x['ports']['in']['@id']] = String

            #loop over out-ports
            myoutputs = dict()
            if type(x['ports']['out']) is list:
                for out_ports in x['ports']['out']:
                    if out_ports['@datatype'] == 'string':
                        myoutputs[out_ports['@id']] = String
            else:
                if x['ports']['out']['@datatype'] == 'string':
                    myoutputs[x['ports']['out']['@id']] = String

        # BeanshellCode task
        if x['@type'] == 'BeanshellCode':
            bnshcode = flow.task[task_name] << BeanshellCode(implementation_code,inputs = myinputs,outputs = myoutputs)
            return bnshcode

        # ExternalTool task
        elif x['@type'] == 'ExternalTool':
            externaltoolcode = flow.task[task_name] << ExternalTool(implementation_code,inputs = myinputs,outputs = myoutputs)
            return externaltoolcode



    def convert(self, sourceFile, t2flow, flowName, compressed, validate, zip):
        import codecs
        import maximal.XMLExport as XMLExport
        
        import xmltodict

        # the code must be put here
        f = open(sourceFile, 'r')

        # parse xmml
        xmml = xmltodict.parse(f)

        # create the workflow from the model
        flow = Workflow(title = xmml['model']['@name'], description = xmml['model']['description'])
        
        # create empty terminals and tasks
        terminals = dict()
        tasks = dict()

        # import definitions
        definitions = xmml['model']['definitions']

        # loop over terminals, submodels
        for type_elem, elem in definitions.items():
            if type_elem == 'terminal':
                if type(elem) is list:
                    for x in elem:
                        terminal = self.create_terminal(x)
                        terminals[x['@id']] = terminal
                else:
                    terminal = self.create_terminal(elem)
                    terminals[elem['@id']] = terminal
            elif type_elem == 'submodel':
                if type(elem) is list:
                    for x in elem:
                        task_name = x['@id']
                        submodel = self.create_submodel(flow, x)
                        tasks[task_name] = submodel
                else:
                    task_name = elem['@id']
                    submodel = self.create_submodel(flow, elem)
                    tasks[task_name] = submodel
            else:
                pass

        # create empty instance
        instances = dict()

        # import topology
        topology = xmml['model']['topology']

        # loop over topology elements (instance and coupling)
        for type_elem_topology, elem_topology in topology.items():
            if type_elem_topology == 'instance':
                for instance in elem_topology:
                    if '@submodel' in instance.keys():
                        myinstance = Instance(kind='submodel', content=instance['@submodel'])
                    elif '@terminal' in instance.keys():
                        myinstance = Instance(kind='terminal', content=instance['@terminal'])
                    instances[instance['@id']] = myinstance
            if type_elem_topology == 'coupling':
                for coupling in elem_topology:
                    data_from = coupling['@from']
                    data_from_instance = data_from.split(".")[0]
                    data_from_port = data_from.split(".")[1]
                    data_to = coupling['@to']
                    data_to_instance = data_to.split(".")[0]
                    data_to_port = data_to.split(".")[1]
                    # coupling from a terminal to a submodel
                    if instances[data_from_instance].kind == 'terminal' and instances[data_to_instance].kind == 'submodel':
                        if terminals[instances[data_from_instance].content].kind == 'source':
                            data_left =  flow.input[data_from_port]
                            data_right = tasks[instances[data_to_instance].content].input[data_to_port]
                            data_left | data_right
                    # coupling from a submodel to a terminal
                    elif instances[data_from_instance].kind == 'submodel' and instances[data_to_instance].kind == 'terminal':
                        if terminals[instances[data_to_instance].content].kind == 'sink':
                            data_left = tasks[instances[data_from_instance].content].output[data_from_port]
                            data_right = flow.output[data_to_port]
                            data_left | data_right
                    # coupling from a submodel to a submodel
                    elif instances[data_from_instance].kind == 'submodel' and instances[data_to_instance].kind == 'submodel':
                        data_left = tasks[instances[data_from_instance].content].output[data_from_port]
                        data_right = tasks[instances[data_to_instance].content].input[data_to_port]
                        data_left | data_right
        
        if validate:
            from t2wrapper import WrapperWorkflow
            flow = WrapperWorkflow(flow, validate, zip)

        UTF8Writer = codecs.getwriter('utf8')
        output = UTF8Writer(t2flow)

        #if compressed:
        #    print 'compressed'
        #    flow.exportXML(XMLExport.XMLExporter(XMLExport.XMLCompressor(output)))
        #else:
        #    print 'not compressed'
        flow.exportXML(XMLExport.XMLExporter(XMLExport.XMLIndenter(output)))

if __name__ == '__main__':
    import argparse
    import os
    import sys
    prog = "./bin/balc" # os.path.basename(os.environ.get('BALCAZAPROG', sys.argv[0]))
    parser = argparse.ArgumentParser(prog=prog, description='Create a Taverna 2 workflow (t2flow) file from a Zapy description file')
    parser.add_argument('--indent', dest='compressed', action='store_false', help='create a larger but more readable indented file')
    parser.add_argument('--validate', dest='validate', action='store_true', help='modify workflow to validate input ports')
    parser.add_argument('--zip', dest='zip', action='store_true', help='create a zip file containing outputs')
    parser.add_argument('--signature', dest='signature', action='store_true', help='print workflow signature')
    parser.add_argument('--flow', dest='flowName', action='store', default='flow', help='name of the workflow in the source file (default: %(default)s)')
    parser.add_argument('source', help='Zapy (.py) description file')
    parser.add_argument('target', nargs='?', help='Taverna 2 Workflow (.t2flow) filename (default: stdout)')
    args = parser.parse_args()
    if args.signature:
        printSig(args.source, args.flowName)
    else:
        target = args.target
        if target is None:
            t2flow = sys.stdout
        else:
            if not target.endswith('.t2flow'):
                target += '.t2flow'
            t2flow = open(target, 'w')
        builder = T2FlowFromXMMLBuilder()
        builder.convert(args.source, t2flow, args.flowName, args.compressed, args.validate, args.zip)
