from core.advbase import *


class Isaac(Adv):
    SAVE_VARIANT = False

    def verdure_zone_scharge(self):
        self.charge_p("verdue_zone_scharge", 0.02, no_autocharge=False)
        self.verdure_team_sp += 2

    def setup_verdure(self, dst="s1"):
        verdure_scharge_self = Timer(lambda _: self.charge_p("verdure_scharge", 0.02, no_autocharge=False), 1.0, True)
        verdure_scharge_self.name = "verdure_scharge"
        verdure_scharge_zone = ZoneTeambuff("verdure_scharge_zone", 0, 10.001, "scharge_p", source=dst)
        verdure_scharge_zone.modifier = Timer(lambda _: self.verdure_zone_scharge(), 1.0, True)
        verdure_scharge_zone.name = "verdure_scharge_zone"
        return (
            (ZoneTeambuff("verdure_str_zone", 0.1, 10, "att", "buff", source=dst), Selfbuff("verdure_str", 0.05, 10, "att", "buff", source=dst)),
            (ZoneTeambuff("verdure_spd_zone", 0.1, 10, "spd", "buff", source=dst), Selfbuff("verdure_spd", 0.05, 10, "spd", "buff", source=dst)),
            (ZoneTeambuff("verdure_regen_zone", 20, 10, "regen", "buff", source=dst), Selfbuff("verdure_regen", 10, 10, "regen", "buff", source=dst)),
            (verdure_scharge_zone, EffectBuff("verdure_scharge", 10.001, verdure_scharge_self.on, verdure_scharge_self.off, source=dst)),
        )

    def prerun(self):
        self.verdure_team_sp = 0
        self.verdure_buff = None  # this is probably fine?

    @staticmethod
    def prerun_skillshare(adv, dst):
        adv.verdure_team_sp = 0
        adv.verdure_buff = None
        adv.rebind_function(Isaac, "verdure_zone_scharge")
        adv.rebind_function(Isaac, "setup_verdure")

    def s1_before(self, e):
        if self.name == "Isaac":
            self.add_amp(max_level=2)
        self.verdure_buff = random.choice(self.setup_verdure(e.name))
        Timer(lambda _: self.verdure_buff[0].on(), 0.9).on()

    def s1_hit5(self, *args):
        self.verdure_buff[1].on()

    def post_run(self, end):
        self.comment = f"total {self.verdure_team_sp}% SP to team from s1"


class Isaac_ALWAYS_STR(Isaac):
    NO_DEPLOY = True
    comment = "s1 always str buff"

    def prerun(self):
        self.verdure_team_sp = 0
        self.verdure_buff = (
            ZoneTeambuff("verdure_str_zone", 0.1, 10, "att", "buff", source="s1"),
            Selfbuff("verdure_str", 0.05, 10, "att", "buff", source="s1"),
        )

    def s1_before(self, e):
        self.add_amp(max_level=2)
        Timer(lambda _: self.verdure_buff[0].on(), 0.9).on()


class Isaac_ALWAYS_SPD(Isaac):
    comment = "s1 always spd buff"

    def prerun(self):
        self.verdure_team_sp = 0
        self.verdure_buff = (
            ZoneTeambuff("verdure_spd_zone", 0.1, 10, "spd", "buff", source="s1"),
            Selfbuff("verdure_spd", 0.05, 10, "spd", "buff", source="s1"),
        )

    def s1_before(self, e):
        self.add_amp(max_level=2)
        Timer(lambda _: self.verdure_buff[0].on(), 0.9).on()


class Isaac_ALWAYS_REGEN(Isaac):
    NO_DEPLOY = True
    comment = "s1 always regen buff"

    def prerun(self):
        self.verdure_team_sp = 0
        self.verdure_buff = (
            ZoneTeambuff("verdure_regen_zone", 20, 10, "regen", "buff", source="s1"),
            Selfbuff("verdure_regen", 10, 10, "regen", "buff", source="s1"),
        )

    def s1_before(self, e):
        self.add_amp(max_level=2)
        Timer(lambda _: self.verdure_buff[0].on(), 0.9).on()


class Isaac_ALWAYS_SCHARGE(Isaac):
    comment = "s1 always skillcharge buff"

    def prerun(self):
        dst = "s1"
        self.verdure_team_sp = 0
        verdure_scharge_self = Timer(lambda _: self.charge_p("verdure_scharge", 0.02, no_autocharge=False), 1.0, True)
        verdure_scharge_self.name = "verdure_scharge"
        verdure_scharge_zone = ZoneTeambuff("verdure_scharge_zone", 0, 10.001, "scharge_p", source=dst)
        verdure_scharge_zone.modifier = Timer(lambda _: self.verdure_zone_scharge(), 1.0, True)
        verdure_scharge_zone.name = "verdure_scharge_zone"
        self.verdure_buff = (
            verdure_scharge_zone,
            EffectBuff("verdure_scharge", 10.001, verdure_scharge_self.on, verdure_scharge_self.off, source=dst),
        )

    def s1_before(self, e):
        self.add_amp(max_level=2)
        Timer(lambda _: self.verdure_buff[0].on(), 0.9).on()


variants = {
    None: Isaac,
    "mass": Isaac,
    "ALLSTR": Isaac_ALWAYS_STR,
    "ALLSPD": Isaac_ALWAYS_SPD,
    "ALLHEAL": Isaac_ALWAYS_REGEN,
    "ALLCHRG": Isaac_ALWAYS_SCHARGE,
}
