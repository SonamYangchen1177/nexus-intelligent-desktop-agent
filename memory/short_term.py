
class ShortTermMemory:

    def __init__(self, max_messages=10):
        self.max_messages = max_messages
        self.messages = []
        self.current_goal = None
        self.current_plan = None
        self.execution_history = []

    def set_goal(self, goal):
        self.current_goal = goal

    def set_plan(self, plan):
        self.current_plan = plan

    def add_message(self, role, content):

        self.messages.append({
            "role": role,
            "content": content
        })

        # Keep only the latest messages
        self.messages = self.messages[
            -self.max_messages:
        ]

    def add_execution(self, record):
        self.execution_history.append(record)

    def get_context(self):

        return {
            "goal": self.current_goal,
            "plan": self.current_plan,
            "messages": self.messages,
            "execution_history": self.execution_history
        }

    def clear(self):

        self.messages = []
        self.current_goal = None
        self.current_plan = None
        self.execution_history = []
