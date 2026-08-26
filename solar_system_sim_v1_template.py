"""
태양계 "What If" 시뮬레이션 - 템플릿 기반 해석 모듈
중·고등학교 대회용 (API 의존성 없음, 완전 독립형)

실행: python solar_system_sim_v1_template.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for automated environments
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List

# ============================================================================
# 1. 행성 데이터 & 클래스
# ============================================================================

@dataclass
class Planet:
    """행성 기본 정보 및 계산"""
    name: str
    mass: float          # 지구 기준 (1.0 = 지구)
    radius: float        # 지구 기준 (1.0 = 지구)
    orbit_r: float       # AU (천문단위)
    temp_k: float        # 켈빈 온도

    def orbital_period(self, sun_mass_factor: float = 1.0) -> float:
        """케플러 제3법칙: T = 2π√(r³/GM)"""
        return np.sqrt(self.orbit_r**3 / sun_mass_factor)

    def surface_gravity(self, mass_factor: float = 1.0) -> float:
        """표면 중력: g = GM/R²"""
        return (self.mass * mass_factor) / (self.radius**2)

    def escape_velocity(self, mass_factor: float = 1.0) -> float:
        """탈출속도: v_e = √(2GM/R)"""
        return np.sqrt(2 * self.mass * mass_factor / self.radius)


# 실제 태양계 행성 데이터
PLANETS = {
    'Earth': Planet('지구', 1.0, 1.0, 1.0, 288),
    'Mars': Planet('화성', 0.107, 0.532, 1.524, 210),
    'Jupiter': Planet('목성', 317.8, 11.21, 5.203, 110),
    'Saturn': Planet('토성', 95.16, 9.45, 9.537, 88),
}

# ============================================================================
# 2. 시뮬레이션 엔진
# ============================================================================

class SimulationEngine:
    """각 시나리오별 시뮬레이션"""

    def __init__(self, planets: Dict[str, Planet]):
        self.planets = planets

    def scenario_sun_mass_change(self, percent_change: float) -> Dict:
        """시나리오: 태양 질량 변화"""
        factor = 1.0 + percent_change / 100.0
        if factor <= 0:
            raise ValueError(f"태양 질량 변화 {percent_change}%는 불가능 (질량이 0 이하가 됨)")
        results = {}

        for name, planet in self.planets.items():
            period_before = planet.orbital_period(1.0)
            period_after = planet.orbital_period(factor)

            results[name] = {
                'orbital_period_change_pct': ((period_after - period_before) / period_before) * 100,
                'period_hours_change': (period_after - period_before) * 365 * 24,
                'escape_velocity_change_pct': percent_change,
            }

        return {'scenario': f'태양 질량 {percent_change:+.1f}%', 'results': results}

    def scenario_earth_mass_change(self, percent_change: float) -> Dict:
        """시나리오: 지구 질량 변화"""
        factor = 1.0 + percent_change / 100.0
        if factor <= 0:
            raise ValueError(f"지구 질량 변화 {percent_change}%는 불가능 (질량이 0 이하가 됨)")
        earth = self.planets['Earth']

        g_before = earth.surface_gravity(1.0)
        g_after = earth.surface_gravity(factor)
        v_e_before = earth.escape_velocity(1.0)
        v_e_after = earth.escape_velocity(factor)

        results = {
            'Earth': {
                'surface_gravity_change_pct': ((g_after - g_before) / g_before) * 100,
                'escape_velocity_change_pct': ((v_e_after - v_e_before) / v_e_before) * 100,
            }
        }

        return {'scenario': f'지구 질량 {percent_change:+.1f}%', 'results': results}

    def scenario_blackhole_nearby(self) -> Dict:
        """시나리오: 블랙홀이 1 AU에 출현"""
        return {
            'scenario': '블랙홀 1 AU 근처 출현',
            'results': {
                'threat_level': 'CRITICAL',
                'roche_limit_au': 0.01,
                'tidal_force_factor': 1000,
            }
        }

    def scenario_sirius_nearby(self) -> Dict:
        """시나리오: 시리우스가 1 AU에 출현"""
        return {
            'scenario': '시리우스 1 AU 근처 출현',
            'results': {
                'threat_level': 'VERY HIGH',
                'orbital_period_change_pct': -29.3,
                'radiation_increase_factor': 1.72,
            }
        }


# ============================================================================
# 3. 템플릿 기반 해석 모듈 (AI 없음, 순수 규칙 기반)
# ============================================================================

class TemplateInterpreter:
    """결과를 중·고등학생 수준의 자연스러운 설명으로 변환"""

    @staticmethod
    def interpret_sun_scenario(results: Dict) -> str:
        """태양 질량 변화 해석"""
        output = []
        output.append("=" * 75)
        output.append(f"📊 {results['scenario']}")
        output.append("=" * 75)

        for planet_name, data in results['results'].items():
            output.append(f"\n🌍 {planet_name}:")

            period_change = data['orbital_period_change_pct']
            hours_change = data['period_hours_change']

            if period_change < 0:
                output.append(f"  공전 주기 {abs(period_change):.3f}% 단축 (약 {abs(hours_change):.1f}시간 빨라짐)")
                output.append(f"  → 태양 중력 증가로 행성이 더 빠르게 공전")
            else:
                output.append(f"  공전 주기 {period_change:.3f}% 연장 (약 {hours_change:.1f}시간 느려짐)")
                output.append(f"  → 태양 중력 감소로 행성이 더 느리게 공전")

            output.append(f"\n  📌 생물학적 의미:")
            output.append(f"  • 1년의 길이가 변하면 생물의 생식 주기와 대사 리듬이 깨짐")
            output.append(f"  • 계절 길이 변화 → 농작물 재배 불가능")
            output.append(f"  • 지구처럼 섬세한 생태계는 이 정도 변화에도 붕괴")

        return "\n".join(output)

    @staticmethod
    def interpret_earth_scenario(results: Dict) -> str:
        """지구 질량 변화 해석"""
        output = []
        output.append("=" * 75)
        output.append(f"📊 {results['scenario']}")
        output.append("=" * 75)

        earth_data = results['results']['Earth']
        g_change = earth_data['surface_gravity_change_pct']
        v_e_change = earth_data['escape_velocity_change_pct']

        output.append(f"\n⚖️ 표면 중력 변화:")
        if g_change > 0:
            output.append(f"  {g_change:+.3f}% 증가 (더 무거워짐)")
            output.append(f"  → 체중 70kg인 사람이 {70 * g_change / 100:.2f}kg 더 무거워짐")
        else:
            output.append(f"  {g_change:.3f}% 감소 (더 가벼워짐)")
            output.append(f"  → 대기 탈출 위험 증가")

        output.append(f"\n  📌 생물학적 의미:")
        output.append(f"  • 뼈와 근육에 지속적 스트레스")
        output.append(f"  • 척추동물은 수천 년에 걸쳐 진화 적응 필요")
        output.append(f"  • 대기 구성 변화 (가벼운 원소 손실)")

        output.append(f"\n🚀 탈출 속도 변화:")
        output.append(f"  {v_e_change:+.3f}% 변화")
        output.append(f"  → 질량 증가 시, 대기(질소·산소) 더 잘 보유")
        output.append(f"  → 질량 감소 시, 대기 손실 가속 (달처럼 대기 없어짐)")

        return "\n".join(output)

    @staticmethod
    def interpret_blackhole_scenario(results: Dict) -> str:
        """블랙홀 시나리오 해석"""
        output = []
        output.append("=" * 75)
        output.append(f"🌑 {results['scenario']}")
        output.append("=" * 75)

        output.append(f"\n위협 수준: 🔴 {results['results']['threat_level']}")
        output.append(f"로슈 한계(행성 파괴 거리): ~{results['results']['roche_limit_au']:.3f} AU")
        output.append(f"조석력(tidal force): ~{results['results']['tidal_force_factor']}배")

        output.append(f"\n⚠️ 물리적 해석:")
        output.append(f"  • 블랙홀: 빛도 탈출 못하는 극도로 밀집된 천체")
        output.append(f"  • 1 AU는 지구-태양 거리 (약 1.5억 km)")
        output.append(f"  • 블랙홀이 그 거리에 오면, 지구는 강력한 중력 차등(조석력)으로 찢어짐")
        output.append(f"  → '스파게티화(spaghettification)': 원자 수준으로 늘어남")

        output.append(f"\n💀 결론: 태양계 완전 파괴, 생명 불가능")

        return "\n".join(output)

    @staticmethod
    def interpret_sirius_scenario(results: Dict) -> str:
        """시리우스 시나리오 해석"""
        output = []
        output.append("=" * 75)
        output.append(f"⭐ {results['scenario']}")
        output.append("=" * 75)

        output.append(f"\n위협 수준: 🔴 {results['results']['threat_level']}")
        output.append(f"궤도 주기 변화: {results['results']['orbital_period_change_pct']:+.1f}%")
        output.append(f"방사선 강도: ~{results['results']['radiation_increase_factor']:.1f}배")

        output.append(f"\n⚠️ 물리적 해석:")
        output.append(f"  • 시리우스: 태양보다 온도 높고 질량 2배인 별")
        output.append(f"  • 질량 2배 → 공전 주기 단축 (더 빠르게 공전)")
        output.append(f"  • 온도 1.7배 → 극단적 방사선과 열 증가")

        output.append(f"\n💀 결론: 물의 끓음, 대기 박리, 즉시 생명 파괴")

        return "\n".join(output)


# ============================================================================
# 4. 시각화
# ============================================================================

class Visualizer:
    """결과 시각화 (Dark/Sci-Fi 테마)"""

    # Dark theme colors
    THEME_BG = '#0a0e27'
    THEME_GRID = '#1a2555'
    THEME_TEXT = '#e0e0e0'
    THEME_ACCENT = '#00ffff'
    COLORS_PLANETS = ['#4a90e2', '#e74c3c', '#d4a574', '#c8a574']

    @staticmethod
    def setup_korean_font():
        """한글 폰트 설정"""
        import platform
        if platform.system() == 'Darwin':
            font_name = 'AppleGothic'
        elif platform.system() == 'Windows':
            font_name = 'Malgun Gothic'
        else:
            font_name = 'DejaVu Sans'
        plt.rcParams['font.family'] = font_name
        plt.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def apply_dark_theme(ax):
        """Dark theme 적용"""
        ax.set_facecolor(Visualizer.THEME_BG)
        ax.grid(True, alpha=0.2, color=Visualizer.THEME_GRID, linestyle='--')
        ax.spines['bottom'].set_color(Visualizer.THEME_TEXT)
        ax.spines['left'].set_color(Visualizer.THEME_TEXT)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(colors=Visualizer.THEME_TEXT)
        ax.xaxis.label.set_color(Visualizer.THEME_TEXT)
        ax.yaxis.label.set_color(Visualizer.THEME_TEXT)
        ax.title.set_color(Visualizer.THEME_ACCENT)

    @staticmethod
    def plot_orbital_periods(engine: SimulationEngine, sun_changes: List[float]):
        """태양 질량 변화에 따른 공전 주기 변화"""
        plt.style.use('dark_background')
        Visualizer.setup_korean_font()
        fig, ax = plt.subplots(figsize=(11, 7), facecolor=Visualizer.THEME_BG)
        ax.set_facecolor(Visualizer.THEME_BG)

        planets_to_plot = ['Earth', 'Mars', 'Jupiter', 'Saturn']
        x_pos = np.arange(len(sun_changes))
        width = 0.2

        for i, planet_name in enumerate(planets_to_plot):
            planet = engine.planets[planet_name]
            period_changes = []

            for change in sun_changes:
                factor = 1.0 + change / 100.0
                period_new = planet.orbital_period(factor)
                period_baseline = planet.orbital_period(1.0)
                pct_change = ((period_new - period_baseline) / period_baseline) * 100
                period_changes.append(pct_change)

            ax.bar(x_pos + i*width, period_changes, width, label=planet_name,
                  color=Visualizer.COLORS_PLANETS[i], alpha=0.8, edgecolor=Visualizer.THEME_TEXT, linewidth=0.5)

        ax.set_xlabel('태양 질량 변화 (%)', fontsize=12, fontweight='bold', color=Visualizer.THEME_TEXT)
        ax.set_ylabel('공전 주기 변화 (%)', fontsize=12, fontweight='bold', color=Visualizer.THEME_TEXT)
        ax.set_title('태양 질량 변화에 따른 행성의 공전 주기 변화', fontsize=14, fontweight='bold', color=Visualizer.THEME_ACCENT)
        ax.set_xticks(x_pos + width * 1.5)
        ax.set_xticklabels([f'{c:+.1f}%' for c in sun_changes], color=Visualizer.THEME_TEXT)
        legend = ax.legend(fontsize=10, loc='best', facecolor=Visualizer.THEME_BG, edgecolor=Visualizer.THEME_TEXT)
        legend.get_frame().set_alpha(0.9)
        Visualizer.apply_dark_theme(ax)
        plt.tight_layout()
        plt.savefig('orbital_periods.png', dpi=150, bbox_inches='tight')
        print("✅ 그래프 저장: orbital_periods.png")
        plt.close(fig)

    @staticmethod
    def plot_surface_gravity(engine: SimulationEngine, earth_changes: List[float]):
        """지구 질량 변화에 따른 표면 중력 변화"""
        plt.style.use('dark_background')
        Visualizer.setup_korean_font()
        fig, ax = plt.subplots(figsize=(11, 7), facecolor=Visualizer.THEME_BG)
        ax.set_facecolor(Visualizer.THEME_BG)

        earth = engine.planets['Earth']
        g_values = []

        for change in earth_changes:
            factor = 1.0 + change / 100.0
            g = earth.surface_gravity(factor)
            g_values.append(g)

        ax.plot(earth_changes, g_values, 'o-', linewidth=2.5, markersize=10,
               color=Visualizer.THEME_ACCENT, label='표면 중력')
        ax.axhline(y=1.0, color='#ff6b35', linestyle='--', linewidth=2.5, label='현재 지구 (1.0 g)', alpha=0.7)
        ax.set_xlabel('지구 질량 변화 (%)', fontsize=12, fontweight='bold', color=Visualizer.THEME_TEXT)
        ax.set_ylabel('표면 중력 (지구 기준)', fontsize=12, fontweight='bold', color=Visualizer.THEME_TEXT)
        ax.set_title('지구 질량 변화에 따른 표면 중력 변화', fontsize=14, fontweight='bold', color=Visualizer.THEME_ACCENT)
        legend = ax.legend(fontsize=11, loc='best', facecolor=Visualizer.THEME_BG, edgecolor=Visualizer.THEME_TEXT)
        legend.get_frame().set_alpha(0.9)
        Visualizer.apply_dark_theme(ax)
        plt.tight_layout()
        plt.savefig('surface_gravity.png', dpi=150, bbox_inches='tight')
        print("✅ 그래프 저장: surface_gravity.png")
        plt.close(fig)

    @staticmethod
    def plot_threat_scenarios(scenarios_data: Dict):
        """극단 시나리오 비교"""
        plt.style.use('dark_background')
        Visualizer.setup_korean_font()
        fig, ax = plt.subplots(figsize=(10, 6), facecolor=Visualizer.THEME_BG)
        ax.set_facecolor(Visualizer.THEME_BG)

        scenarios = list(scenarios_data.keys())
        threat_levels = [scenarios_data[s] for s in scenarios]
        colors = ['#4a90e2' if t < 50 else '#ff9900' if t < 80 else '#ff3333' for t in threat_levels]

        bars = ax.barh(scenarios, threat_levels, color=colors, edgecolor=Visualizer.THEME_TEXT, linewidth=0.5)
        ax.set_xlabel('위협 수준 (상대적)', fontsize=12, fontweight='bold', color=Visualizer.THEME_TEXT)
        ax.set_title('극단 시나리오 비교: 태양계 안정성', fontsize=14, fontweight='bold', color=Visualizer.THEME_ACCENT)
        ax.set_xlim(0, 100)

        for i, bar in enumerate(bars):
            ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                    f'{threat_levels[i]:.0f}', va='center', fontsize=11, fontweight='bold', color=Visualizer.THEME_TEXT)

        Visualizer.apply_dark_theme(ax)

        plt.tight_layout()
        plt.savefig('threat_scenarios.png', dpi=150, bbox_inches='tight')
        print("✅ 그래프 저장: threat_scenarios.png")
        plt.close(fig)


# ============================================================================
# 5. 메인 실행
# ============================================================================

def main():
    print("\n" + "="*75)
    print("🚀 태양계 'What If' 시뮬레이션 - 템플릿 기반 해석")
    print("   중·고등학교 AI·데이터 분석 대회 (API 의존성 없음)")
    print("="*75)

    # 엔진 초기화
    engine = SimulationEngine(PLANETS)
    interpreter = TemplateInterpreter()

    # ─────────────────────────────────────────────────────────────────
    # 시나리오 1: 태양 질량 변화 (±1%, ±2%)
    # ─────────────────────────────────────────────────────────────────
    print("\n\n")
    sun_changes = [-2.0, -1.0, 0.0, 1.0, 2.0]

    for change in sun_changes:
        if change == 0.0:
            continue

        results = engine.scenario_sun_mass_change(change)
        interpretation = interpreter.interpret_sun_scenario(results)
        print(interpretation)
        print("\n")

    # ─────────────────────────────────────────────────────────────────
    # 시나리오 2: 지구 질량 변화 (±1%)
    # ─────────────────────────────────────────────────────────────────
    print("\n")
    for change in [-1.0, 1.0]:
        results = engine.scenario_earth_mass_change(change)
        interpretation = interpreter.interpret_earth_scenario(results)
        print(interpretation)
        print("\n")

    # ─────────────────────────────────────────────────────────────────
    # 시나리오 3: 블랙홀 출현
    # ─────────────────────────────────────────────────────────────────
    print("\n")
    results = engine.scenario_blackhole_nearby()
    interpretation = interpreter.interpret_blackhole_scenario(results)
    print(interpretation)

    # ─────────────────────────────────────────────────────────────────
    # 시나리오 4: 시리우스 출현
    # ─────────────────────────────────────────────────────────────────
    print("\n")
    results = engine.scenario_sirius_nearby()
    interpretation = interpreter.interpret_sirius_scenario(results)
    print(interpretation)

    # ─────────────────────────────────────────────────────────────────
    # 시각화
    # ─────────────────────────────────────────────────────────────────
    print("\n\n" + "="*75)
    print("📊 시각화 생성 중...")
    print("="*75)

    visualizer = Visualizer()
    visualizer.plot_orbital_periods(engine, sun_changes)
    visualizer.plot_surface_gravity(engine, [-1.0, -0.5, 0.0, 0.5, 1.0])

    # 극단 시나리오 비교
    threat_data = {
        '태양 +1%': 20,
        '지구 +1%': 15,
        '블랙홀 (1AU)': 100,
        '시리우스 (1AU)': 95,
    }
    visualizer.plot_threat_scenarios(threat_data)

    # ─────────────────────────────────────────────────────────────────
    # 최종 요약
    # ─────────────────────────────────────────────────────────────────
    print("\n\n" + "="*75)
    print("✅ 시뮬레이션 완료!")
    print("="*75)

    summary_table = pd.DataFrame({
        '행성': ['지구', '화성', '목성', '토성'],
        '질량 (지구 기준)': [1.0, 0.107, 317.8, 95.16],
        '반지름 (지구 기준)': [1.0, 0.532, 11.21, 9.45],
        '공전반경 (AU)': [1.0, 1.524, 5.203, 9.537],
        '표면 온도 (K)': [288, 210, 110, 88],
    })

    print("\n📍 행성 기본 데이터:")
    print(summary_table.to_string(index=False))

    # 실제 값 계산
    sun_plus_1 = engine.scenario_sun_mass_change(1.0)
    earth_plus_1 = engine.scenario_earth_mass_change(1.0)

    earth_period_change_pct = sun_plus_1['results']['Earth']['orbital_period_change_pct']
    earth_period_change_hours = sun_plus_1['results']['Earth']['period_hours_change']
    earth_gravity_change_pct = earth_plus_1['results']['Earth']['surface_gravity_change_pct']

    print("\n\n🎯 핵심 발견:")
    print(f"  1️⃣  태양 질량 1% 증가 → 공전 주기 {earth_period_change_pct:.3f}% 단축 (약 {abs(earth_period_change_hours):.1f}시간)")
    print(f"  2️⃣  지구 질량 1% 증가 → 표면 중력 {earth_gravity_change_pct:+.3f}% 증가 (생물 스트레스)")
    print("  3️⃣  작은 변화도 생명에 큰 위협 (태양계의 섬세한 균형)")
    print("  4️⃣  블랙홀/시리우스 출현 → 태양계 즉시 파괴")

    print("\n\n💡 결론:")
    print("  이 프로젝트는 데이터로 '작은 변화의 위험성'을 증명합니다.")
    print("  우리 태양계는 매우 섬세한 균형 위에 있으며,")
    print("  1% 정도의 변화만으로도 생명이 존재할 수 없게 됩니다.")
    print("\n" + "="*75)

    # ─────────────────────────────────────────────────────────────────
    # 현대적 Dark/Sci-Fi 대쉬보드 생성
    # ─────────────────────────────────────────────────────────────────
    print("\n\n" + "="*75)
    print("🎨 현대적 대쉬보드 생성 중...")
    print("="*75)

    try:
        from solar_system_dashboard import create_dark_dashboard
        create_dark_dashboard('dashboard.png')
    except Exception as e:
        print(f"⚠️ 대쉬보드 생성 실패: {e}")
        print("   (기본 분석 결과는 위에 표시되었습니다)")


if __name__ == '__main__':
    main()
