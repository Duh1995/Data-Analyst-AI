class ConversationManager:
    def __init__(self, max_interactions=5):
        self.max_interactions = max_interactions
        self.history = []

    def get_history(self):
        return list(self.history)

    def add_interaction(self, question, answer):
        self.history.extend([
            {
                "role": "user",
                "content": question
            },
            {
                "role": "assistant",
                "content": answer
            }
        ])

        max_messages = self.max_interactions * 2

        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]

    def reset(self):
        self.history = []
