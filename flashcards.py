


class Card:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer

    def get_question(self):
        return self.question

    def get_answer(self):
        return self.answer

    def set_question(self, question):
        self.question = question

    def set_answer(self, answer):
        self.answer = answer