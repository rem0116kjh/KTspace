"""태양계 'What If' 시뮬레이션 결과 대시보드.

블랙홀·시리우스 같은 천체가 가까이 나타나거나 질량이 변했을 때의
영향을 초보자도 시나리오 → 변화 → 결과 순서로 읽을 수 있게 보여준다.
"""

from typing import Dict, Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


COLORS = {
    "bg": "#060D18",
    "surface": "#0E1B2C",
    "surface_alt": "#14243A",
    "border": "#293E59",
    "text": "#F5F7FB",
    "muted": "#A7B4C5",
    "primary": "#68D4C4",
    "blue": "#6EA8FE",
    "warning": "#FFB45E",
    "danger": "#FF6678",
    "danger_dark": "#6F2432",
}

SCENARIOS = [
    {"name": "태양 질량 +1%", "kind": "미세 변화", "threat": 20,
     "result": "공전 주기 약 0.5% 단축", "color": COLORS["blue"]},
    {"name": "지구 질량 +1%", "kind": "미세 변화", "threat": 15,
     "result": "표면 중력 약 1% 증가", "color": COLORS["primary"]},
    {"name": "블랙홀 10M☉ · 1 AU", "kind": "극단 변화", "threat": 100,
     "result": "중력 10배 · 궤도 붕괴", "color": COLORS["danger"]},
    {"name": "시리우스 1 AU", "kind": "극단 변화", "threat": 95,
     "result": "극심한 열 · 궤도 불안정", "color": COLORS["warning"]},
]


class SolarSystemDashboard:
    """선택한 가상 시나리오의 원인과 결과를 설명하는 대시보드."""

    def __init__(self, figsize=(20, 12), dpi=100):
        self.figsize, self.dpi, self.fig = figsize, dpi, None
        self.setup_style()

    def setup_style(self):
        import platform

        font_name = {"Darwin": "AppleGothic", "Windows": "Malgun Gothic"}.get(
            platform.system(), "DejaVu Sans"
        )
        plt.rcParams.update({
            "figure.facecolor": COLORS["bg"],
            "axes.facecolor": COLORS["bg"],
            "axes.edgecolor": COLORS["border"],
            "text.color": COLORS["text"],
            "font.family": font_name,
            "font.size": 10,
            "axes.unicode_minus": False,
        })

    @staticmethod
    def _panel(ax, edge=COLORS["border"], face=COLORS["surface"]):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(FancyBboxPatch(
            (0.006, 0.006), 0.988, 0.988,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            facecolor=face, edgecolor=edge, linewidth=1.2,
            transform=ax.transAxes,
        ))

    def create_dashboard(self, scenarios_data: Optional[Dict] = None):
        self.fig = plt.figure(figsize=self.figsize, dpi=self.dpi, facecolor=COLORS["bg"])
        gs = GridSpec(
            3, 3, figure=self.fig, height_ratios=[0.52, 2.15, 0.92],
            width_ratios=[1.25, 1.15, 0.9], left=0.045, right=0.955,
            top=0.82, bottom=0.055, hspace=0.15, wspace=0.12,
        )
        self.add_title()

        tabs = gs[0, :].subgridspec(1, 4, wspace=0.08)
        for index, scenario in enumerate(SCENARIOS):
            self.draw_scenario_tab(self.fig.add_subplot(tabs[index]), scenario,
                                   selected=scenario["name"].startswith("블랙홀"))

        self.draw_blackhole_scene(self.fig.add_subplot(gs[1, :2]))
        self.draw_impact_summary(self.fig.add_subplot(gs[1, 2]))
        self.draw_scenario_comparison(self.fig.add_subplot(gs[2, :]))
        return self.fig

    def add_title(self):
        self.fig.text(0.05, 0.955, "태양계 WHAT IF 실험실", ha="left", va="top",
                      fontsize=28, fontweight="bold", color=COLORS["text"])
        self.fig.text(0.05, 0.905,
                      "만약 낯선 천체가 나타나거나 질량이 달라진다면, 태양계에는 무슨 일이 생길까요?",
                      ha="left", va="top", fontsize=12.5, color=COLORS["muted"])
        self.fig.text(0.95, 0.94, "가상 시나리오 · 실제 발생 예측 아님",
                      ha="right", va="top", fontsize=9.5, color=COLORS["warning"],
                      bbox={"boxstyle": "round,pad=0.5", "fc": COLORS["surface"],
                            "ec": COLORS["warning"], "lw": 1.0})
        self.fig.text(0.05, 0.855, "① 실험할 상황을 고르세요", ha="left", va="top",
                      fontsize=13.5, fontweight="bold", color=COLORS["text"])

    def draw_scenario_tab(self, ax, scenario: Dict, selected=False):
        edge = scenario["color"] if selected else COLORS["border"]
        face = COLORS["surface_alt"] if selected else COLORS["surface"]
        self._panel(ax, edge=edge, face=face)
        ax.add_patch(Circle((0.08, 0.56), 0.022, color=scenario["color"], transform=ax.transAxes))
        ax.text(0.14, 0.65, scenario["name"], fontsize=11.3, fontweight="bold",
                color=COLORS["text"], va="center")
        ax.text(0.14, 0.34, scenario["kind"], fontsize=8.8, color=COLORS["muted"], va="center")
        if selected:
            ax.text(0.92, 0.50, "선택됨", ha="right", va="center", fontsize=8.5,
                    color=COLORS["danger"], fontweight="bold")

    def draw_blackhole_scene(self, ax):
        ax.set_xlim(-6.4, 6.4)
        ax.set_ylim(-3.7, 3.7)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor(COLORS["surface"])
        for spine in ax.spines.values():
            spine.set_color(COLORS["danger_dark"])
            spine.set_linewidth(1.4)

        ax.set_title("② 만약 10 태양질량 블랙홀이 지구에서 1 AU 거리에 나타난다면?",
                     loc="left", pad=14, fontsize=15.5, fontweight="bold",
                     color=COLORS["text"])

        rng = np.random.default_rng(12)
        ax.scatter(rng.uniform(-6.2, 6.2, 130), rng.uniform(-3.5, 3.5, 130),
                   s=rng.uniform(1, 5, 130), color="#DDE8F8", alpha=0.20, zorder=0)

        # 지구
        earth_x = -3.65
        ax.add_patch(Circle((earth_x, 0), 0.52, color="#4F93E8", ec="#CDE3FF", lw=1.4, zorder=5))
        ax.add_patch(patches.Ellipse((earth_x - 0.1, 0.07), 0.22, 0.45,
                                     angle=28, color="#73C77B", alpha=0.9, zorder=6))
        ax.text(earth_x, -0.86, "지구", ha="center", fontsize=11.5,
                color=COLORS["blue"], fontweight="bold")

        # 블랙홀과 강착원반
        bh_x = 3.65
        ax.add_patch(patches.Ellipse((bh_x, 0), 3.0, 0.68, angle=-8,
                                     facecolor=COLORS["warning"], alpha=0.18,
                                     edgecolor=COLORS["warning"], lw=1.4, zorder=3))
        ax.add_patch(patches.Ellipse((bh_x, 0), 2.1, 0.38, angle=-8,
                                     fill=False, edgecolor=COLORS["danger"], lw=2.0, zorder=4))
        ax.add_patch(Circle((bh_x, 0), 0.75, color="#010205", ec=COLORS["danger"], lw=1.6, zorder=5))
        ax.add_patch(Circle((bh_x, 0), 0.98, fill=False, ec=COLORS["danger"], lw=1.0, alpha=0.35, zorder=4))
        ax.text(bh_x, -1.15, "블랙홀", ha="center", fontsize=11.5,
                color=COLORS["danger"], fontweight="bold")

        # 거리와 중력 영향
        ax.annotate("", xy=(2.65, 2.35), xytext=(-3.15, 2.35),
                    arrowprops={"arrowstyle": "<->", "color": COLORS["muted"], "lw": 1.2})
        ax.text(-0.25, 2.55, "1 AU  ≈  1억 5천만 km", ha="center", fontsize=10,
                color=COLORS["muted"])
        ax.add_patch(FancyArrowPatch((-3.15, 0.24), (-1.55, 0.72),
                                     arrowstyle="-|>", mutation_scale=18,
                                     color=COLORS["danger"], lw=2.0))
        ax.text(-3.25, 1.25, "태양보다 약 10배 강한 중력\n→ 기존 공전 궤도를 크게 교란",
                ha="center", fontsize=9.5, color=COLORS["danger"], linespacing=1.35)

        ax.text(0.025, 0.035,
                "쉽게 말하면: 1 AU에서는 지구가 즉시 찢어지기보다, 갑자기 추가된 강한 중력 때문에 태양계 궤도가 무너집니다.",
                transform=ax.transAxes, fontsize=9.3, color=COLORS["text"],
                bbox={"boxstyle": "round,pad=0.5", "fc": COLORS["bg"],
                      "ec": COLORS["border"], "alpha": 0.96})

    def draw_impact_summary(self, ax):
        self._panel(ax, edge=COLORS["danger"])
        ax.text(0.075, 0.92, "③ 예상되는 변화", fontsize=14.5,
                fontweight="bold", color=COLORS["text"])
        ax.text(0.075, 0.835, "교육용 상대 위험 지수", fontsize=9.5, color=COLORS["muted"])
        ax.text(0.925, 0.835, "100 / 100", ha="right", fontsize=12,
                color=COLORS["danger"], fontweight="bold")
        ax.add_patch(FancyBboxPatch((0.075, 0.775), 0.85, 0.025,
                                    boxstyle="round,pad=0.002", fc=COLORS["border"], ec="none"))
        ax.add_patch(FancyBboxPatch((0.075, 0.775), 0.85, 0.025,
                                    boxstyle="round,pad=0.002", fc=COLORS["danger"], ec="none"))

        impacts = [
            ("블랙홀 중력", "태양의 약 10배", "같은 1 AU 거리에서 단순 비교"),
            ("조석력", "태양의 약 10배", "직접 파괴보다 궤도 교란이 핵심"),
            ("태양계", "심각한 궤도 붕괴", "기존 공전 균형을 유지하기 어려움"),
        ]
        y = 0.66
        for label, value, help_text in impacts:
            ax.text(0.075, y, label, fontsize=9.2, color=COLORS["muted"])
            ax.text(0.925, y, value, ha="right", fontsize=11,
                    color=COLORS["text"], fontweight="bold")
            ax.text(0.075, y - 0.065, help_text, fontsize=8.5, color=COLORS["muted"])
            y -= 0.16

        ax.text(0.075, 0.155, "결론", fontsize=9.2, color=COLORS["muted"])
        ax.text(0.075, 0.095, "현재 궤도 유지 불가능", fontsize=14.5,
                color=COLORS["danger"], fontweight="bold")
        ax.text(0.075, 0.035, "※ 10 태양질량·1 AU·갑작스런 출현을 가정한 단순 모델입니다.",
                fontsize=7.9, color=COLORS["muted"])

    def draw_scenario_comparison(self, ax):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(0, 0.96, "④ 다른 상황과 위험도 비교", fontsize=14.5,
                fontweight="bold", color=COLORS["text"], va="top")
        ax.text(1, 0.96, "낮음  0  ─────────  100  높음", ha="right", va="top",
                fontsize=8.8, color=COLORS["muted"])

        gap = 0.012
        width = (1 - gap * 3) / 4
        for index, scenario in enumerate(SCENARIOS):
            x = index * (width + gap)
            selected = scenario["name"].startswith("블랙홀")
            ax.add_patch(FancyBboxPatch(
                (x, 0.06), width, 0.69,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                fc=COLORS["surface_alt"] if selected else COLORS["surface"],
                ec=scenario["color"] if selected else COLORS["border"],
                lw=1.8 if selected else 1.0,
            ))
            ax.text(x + 0.018, 0.64, scenario["name"], fontsize=10.2,
                    fontweight="bold", color=COLORS["text"])
            ax.text(x + width - 0.018, 0.64, str(scenario["threat"]),
                    ha="right", fontsize=12.5, fontweight="bold", color=scenario["color"])
            ax.add_patch(FancyBboxPatch((x + 0.018, 0.43), width - 0.036, 0.055,
                                        boxstyle="round,pad=0.002", fc=COLORS["border"], ec="none"))
            bar_width = (width - 0.036) * scenario["threat"] / 100
            ax.add_patch(FancyBboxPatch((x + 0.018, 0.43), bar_width, 0.055,
                                        boxstyle="round,pad=0.002", fc=scenario["color"], ec="none"))
            ax.text(x + 0.018, 0.23, scenario["result"], fontsize=8.7,
                    color=COLORS["muted"])

    # 이전 대시보드의 공개 메서드 이름과 호환한다.
    def draw_solar_system(self, ax):
        self.draw_blackhole_scene(ax)

    def draw_system_info(self, ax, data: Optional[Dict] = None):
        self.draw_impact_summary(ax)

    def draw_simulation_stats(self, ax, data: Optional[Dict] = None):
        self.draw_impact_summary(ax)

    def draw_planet_summary(self, ax):
        self.draw_scenario_comparison(ax)


def create_dark_dashboard(output_file: str = "dashboard.png"):
    dashboard = SolarSystemDashboard(figsize=(20, 12), dpi=150)
    fig = dashboard.create_dashboard()
    fig.savefig(output_file, facecolor=COLORS["bg"], edgecolor="none", dpi=150)
    print(f"✅ 대시보드 저장: {output_file}")
    plt.close(fig)


if __name__ == "__main__":
    create_dark_dashboard()
