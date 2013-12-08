from t2activity import NestedWorkflow
from t2types import ListType, String
from t2flow import Workflow

class WrapperWorkflow(Workflow):

	def __init__(self, flow):
		self.flow = flow
		Workflow.__init__(self, flow.title, flow.author, flow.description)
		setattr(self.task, flow.name, NestedWorkflow(flow))
		nested = getattr(self.task, flow.name)
		for port in flow.input:
			# Set type to same depth, but basetype of String
			depth = port.type.getDepth()
			if depth == 0:
				type = String
			else:
				type = ListType(String, depth)
			# Copy any annotations
			type.dict = port.type.dict
			setattr(self.input, port.name, type)
			getattr(self.input, port.name) >> getattr(nested.input, port.name)
		for port in flow.output:
			# Set type to same depth, but basetype of String
			depth = port.type.getDepth()
			if depth == 0:
				type = String
			else:
				type = ListType(String, depth)
			# Copy any annotations
			type.dict = port.type.dict
			setattr(self.output, port.name, type)
			getattr(nested.output, port.name) >> getattr(self.output, port.name)
