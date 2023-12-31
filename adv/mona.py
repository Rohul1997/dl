from core.advbase import *
from module.template import Adv_INFUTP


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
                self.conf.s1_ddrive.attr = self.conf.s1_ddrive.attr_PLUS
            else:
                log("s1_ddrive", "variant", "base")
                self.conf.s1_ddrive.attr = self.conf.s1_ddrive.attr_BASE


class Mona_INFUTP(Mona, Adv_INFUTP):
    pass


variants = {None: Mona, "RNG": Mona_RNG, "INFUTP": Mona_INFUTP}
