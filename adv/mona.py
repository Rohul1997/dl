from core.advbase import *


class Mona(Adv):
    def prerun(self):
        self.beast_eye = Selfbuff("beast_eye", 0.2, 30, "utph", "buff").ex_bufftime()
        Event("dragon").listener(self.ddrive_buff_off)

    def fs_proc(self, e):
        if self.nihilism:
            return
        self.beast_eye.on()

    def ddrive_buff_off(self, e):
        self.beast_eye.off()


class Mona_RNG(Mona):
    def s1_before(self, e):
        if e.group == "ddrive":
            if random.random() <= 0.25:
                log("s1_ddrive", "variant", "plus")
                self.conf.s1_ddrive.attr = self.conf.s1_ddrive.attr_plus
            else:
                log("s1_ddrive", "variant", "base")
                self.conf.s1_ddrive.attr = self.conf.s1_ddrive.attr_base


class Mona_PERSONA(Mona):
    SAVE_VARIANT = False
    comment = "infinite persona gauge"

    def prerun(self):
        super().prerun()
        self.dragondrive = self.dragonform.set_dragondrive(ModeManager(group="ddrive", x=True, fs=True, s1=True, s2=True), drain=75, infinite=True)
        self.dragonform.charge_gauge(3000, utp=True, dhaste=False)


variants = {None: Mona, "RNG": Mona_RNG, "PERSONA": Mona_PERSONA}
