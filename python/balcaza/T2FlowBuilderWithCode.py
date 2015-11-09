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
      self._ports = {'_out' : {}, '_in' : {}}
      self._kind = kind
    
    def set_type(self, kind):
      self._kind = kind
    
    def add_port(self, port_id, port_value):
        if self._kind == 'source':
          self._ports['_out'][port_id] = port_value
        elif self._kind == 'sink':
          self._ports['_in'][port_id] = port_value
        else:
	  raise Exception('Error: the kind of terminal is not set!')


class T2FlowBuilder:

    def convert(self, sourceFile, t2flow, flowName, compressed, validate, zip):
        import codecs
        import maximal.XMLExport as XMLExport
        
        import xmltodict

        # the code must be put here
        f = open("/home/adminuser/Software/balcazapy/examples/xmml/hello_world/hello_world_2.xml", 'r')
        xmml = xmltodict.parse(f)
        #print xmml
        
        from balcaza.t2types import *
        from balcaza.t2activity import *
        from balcaza.t2flow import Workflow

        # create the workflow from the model
        flow = Workflow(title = xmml['model']['@name'], description = xmml['model']['description'])
        
        # create tasks
        terminals = dict()
        nsubmodels = dict()
        mytask = dict()
        
        nelements =  len (xmml['model']['definitions'])
        definitions = xmml['model']['definitions']

        for type_elem, elem in definitions.items():
            if type_elem == 'terminal':
                if type(elem) is list:
                    for x in elem:
                        #print x
                        terminal = Terminal(kind=x['@type'])
                        if 'out' in x['ports'].keys():
                            if type(x['ports']['out']) is list:
                                for pp in x['ports']['out']:
                                    port_id = pp['@id']
                                    port_value = {'datatype' : pp['@datatype']}
                                    terminal.add_port(port_id, port_value)
                            else:
                                port_id = x['ports']['out']['@id']
                                port_value = {'datatype' : x['ports']['out']['@datatype']}
                                terminal.add_port(port_id, port_value)
                        if 'in' in x['ports'].keys():
                            if type(x['ports']['in']) is list:
                                for pp in x['ports']['in']:
                                    port_id = pp['@id']
                                    port_value = {'datatype' : pp['@datatype']}
                                    terminal.add_port(port_id, port_value)
                            else:
                                port_id = x['ports']['in']['@id']
                                port_value = {'datatype' : x['ports']['in']['@datatype']}
                                terminal.add_port(port_id, port_value)
                        terminal.add_port
                        terminals[x['@id']] = terminal
                else:
                    b = 2
            if type_elem == 'submodel':
                if type(elem) is list:
                    for x in elem:
                        implementation_code  = str(x['implementation']['code']['#text'])
                        task_name = x['@id']
                        if x['@type'] == 'BeanshellCode':
                            #loop over in-ports
                            myinputs = dict()
                            if type(x['ports']['in']) is list:
                                for in_ports in x['ports']['in']:
                                    #print in_ports
                                    if in_ports['@datatype'] == 'string':
                                        myinputs[in_ports['@id']] = String
                            else:
                                if x['ports']['in']['@datatype'] == 'string':
                                    myoutputs[elem['ports']['in']['@id']] = String

                            #loop over out-ports
                            myoutputs = dict()
                            if type(x['ports']['out']) is list:
                                for out_ports in x['ports']['out']:
                                    print out_ports
                                    if out_ports['@datatype'] == 'string':
                                        myoutputs[out_ports['@id']] = String
                            else:
                                if x['ports']['out']['@datatype'] == 'string':
                                    myoutputs[x['ports']['out']['@id']] = String

                        if x['@type'] == 'BeanshellCode':
                            # BeanshellCode task
                            bnshcode = flow.task[task_name] << BeanshellCode(implementation_code,
                                                                         inputs = myinputs,
                                                                         outputs = myoutputs
                            )
                            mytask[task_name] = bnshcode
                        elif x['@type'] == 'ExternalTool':
                            # ExternalTool task
                            externaltoolcode = flow.task[task_name] << ExternalTool(implementation_code,
                                                                         inputs = myinputs,
                                                                         outputs = myoutputs
                            )
                            mytask[task_name] = externaltoolcode
                else:
                    implementation_code  = str(elem['implementation']['code']['#text'])
                    task_name = elem['@id']
                    if elem['@type'] == 'BeanshellCode' or elem['@type'] == 'ExternalTool':
                        #print elem
                        # ports
                        #print elem['ports']['in']
                        #loop over in-ports
                        myinputs = dict()
                        if type(elem['ports']['in']) is list:
                            for in_ports in elem['ports']['in']:
                                #print in_ports
                                if in_ports['@datatype'] == 'string':
                                    myinputs[in_ports['@id']] = String
                        else:
                            if elem['ports']['in']['@datatype'] == 'string':
                                myoutputs[elem['ports']['in']['@id']] = String

                        #loop over out-ports
                        myoutputs = dict()
                        if type(elem['ports']['out']) is list:
                            for out_ports in elem['ports']['out']:
                                print out_ports
                                if out_ports['@datatype'] == 'string':
                                    myoutputs[out_ports['@id']] = String
                        else:
                            if elem['ports']['out']['@datatype'] == 'string':
                                myoutputs[elem['ports']['out']['@id']] = String

                        if elem['@type'] == 'BeanshellCode':
                            # BeanshellCode task
                            bnshcode = flow.task[task_name] << BeanshellCode(implementation_code,
                                                                         inputs = myinputs,
                                                                         outputs = myoutputs
                            )
                            mytask[task_name] = bnshcode
                        elif elem['@type'] == 'ExternalTool':
                            # ExternalTool task
                            externaltoolcode = flow.task[task_name] << ExternalTool(implementation_code,
                                                                         inputs = myinputs,
                                                                         outputs = myoutputs
                            )
                            mytask[task_name] = externaltoolcode
                    else:
                        raise Exception('The submodel type does not exist')


        # link the tasks
        #print terminals
        #print xmml['model']['topology']
        myinstances = dict()
        # elem_top contains in two different dictionaries 
        for type_top, elem_top in xmml['model']['topology'].items():
            if type_top == 'instance':
                for instance in elem_top:
                    #print instance
                    #print instance['@id']
                    if '@submodel' in instance.keys():
                        single_instance = ('submodel', instance['@submodel'])
                    elif '@terminal' in instance.keys():
                        single_instance = ('terminal', instance['@terminal'])
                    myinstances[instance['@id']] = single_instance
            if type_top == 'coupling':
                for coupling in elem_top:
                    data_from = coupling['@from']
                    data_from_instance = data_from.split(".")[0]
                    data_from_port = data_from.split(".")[1]
                    data_to = coupling['@to']
                    data_to_instance = data_to.split(".")[0]
                    data_to_port = data_to.split(".")[1]
                    #print data_from
                    #print data_to
                    # coupling from a terminal to a submodel
                    if myinstances[data_from_instance][0] == 'terminal' and myinstances[data_to_instance][0] == 'submodel':
                        #print terminals[myinstances[data_from_instance][1]]
                        #print mytask[myinstances[data_to_instance][1]]
                        if terminals[myinstances[data_from_instance][1]]._kind == 'source':
                            data_left =  flow.input[data_from_port]
                            data_right = mytask[myinstances[data_to_instance][1]].input[data_to_port]
                            data_left | data_right
                    # coupling from a submodel to a terminal
                    elif myinstances[data_from_instance][0] == 'submodel' and myinstances[data_to_instance][0] == 'terminal':
                        if terminals[myinstances[data_to_instance][1]]._kind == 'sink':
                            data_left = mytask[myinstances[data_from_instance][1]].output[data_from_port]
                            data_right = flow.output[data_to_port]
                            data_left | data_right
                    # coupling from a submodel to a submodel
                    elif myinstances[data_from_instance][0] == 'submodel' and myinstances[data_to_instance][0] == 'submodel':
                        data_left = mytask[myinstances[data_from_instance][1]].output[data_from_port]
                        data_right = mytask[myinstances[data_to_instance][1]].input[data_to_port]
                        data_left | data_right
        
        #a = mytask['HW1']
        #flow.input['stringaaa1'] | a.input['string1']
        #flow.input['strinaaag2'] | a.input['string2']
        #a = bnshcode.output.outputstr
        #b = flow.output['output_str']
        #a | b
        #bnshcode.output.outputstr | flow.output.output_str    
        ##flow = readZapyFile(sourceFile, flowName)

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
        builder = T2FlowBuilder()
        builder.convert(args.source, t2flow, args.flowName, args.compressed, args.validate, args.zip)
