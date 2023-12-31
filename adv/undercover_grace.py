from core.advbase import *


class Undercover_Grace(Adv):
    def prerun(self):
        self.soul_seal_buff = MultiLevelBuff(
            "soul_seal",
            [Selfbuff(f"soul_seal_lv{lv+1}", buffvalue, -1, "ex", "actdown", source="a1") for lv, buffvalue in enumerate((0.10, 0.15, 0.20, 0.80))],
        )
        Event("dragon").listener(self.a1_reset)
        self.a3_regen = Timer(self.a3_regen, 2.9, True).on()
        o_s2_check = self.a_s_dict["s2"].check
        self.a_s_dict["s2"].check = lambda: o_s2_check() and self.soul_seal_buff.get()

    @property
    def soul_seal(self):
        return self.soul_seal_buff.level

    def fs_before(self, e):
        if self.soul_seal == 4:
            self.add_hp(-2)

    def x_before(self, e):
        if self.soul_seal == 4:
            self.add_hp(-2)

    def s_hp_check(self, e):
        if self.soul_seal == 4 and e.name in self.damage_sources:
            self.add_hp(-2)

    def add_combo(self, name="#"):
        result = super().add_combo(name=name)
        if name.startswith("s1"):
            for _ in range(self.echo):
                self.soul_seal_buff.on()
        return result

    def a1_reset(self, e):
        self.soul_seal_buff.off()

    def s2_before(self, e):
        Timer(self.a1_reset, 1.5).on()

    def a3_regen(self, t):
        if self.amp_lvl(kind="team", key=3) >= 1:
            self.heal_make("a3_regen", 5)


variants = {None: Undercover_Grace}
