
class Settings:

    def __init__(self, guild, user):
        self.guild = guild
        self.user = user
        self.auto_t = False
        self.translit = False
        self.def_lang = "Spanish"
        self.tgt_lang = "English"

    def set_auto_t(self, value):
        self.auto_t = value

    def set_translit(self, value):
        self.translit = value

    def set_def_lang(self, value):
        self.def_lang = value

    def set_tgt_lang(self, value):
        self.tgt_lang = value
       
        
    def get_auto_t(self):
        return self.auto_t

    def get_translit(self):
        return self.translit

    def get_def_lang(self):
        return self.def_lang

    def get_tgt_lang(self):
        return self.tgt_lang
