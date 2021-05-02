from core.advbase import *


class Yoshitsune(Adv):
    comment = "no counter on s1/dodge"

    def prerun(self):
        Event("dodge").listener(self.l_dodge_attack, order=0)
        self.allow_dodge = False

    def l_dodge_attack(self, e):
        log("cast", "dodge_attack")
        for _ in range(7):
            self.add_combo("dodge")
            self.dmg_make("dodge", 0.10)
        if self.nihilism:
            return
        if self.allow_dodge and not self.is_set_cd("a1", 5):
            self.hitattr_make("dodge", "dodge", "default", 0, self.conf.dodge.attr_spd)


class Yoshitsune_COUNTER(Yoshitsune):
    comment = "always counter on s1/dodge"

    def prerun(self):
        super().prerun()
        self.conf.s1.attr = self.conf.s1.attr_counter
        self.allow_dodge = True


variants = {None: Yoshitsune, "COUNTER": Yoshitsune_COUNTER}
