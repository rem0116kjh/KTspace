"""Shared, dependency-free physics used by both lab interfaces."""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

# 시나리오 타입 열거형 (magic string 제거)
class ScenarioType(Enum):
    """시나리오 타입을 문자열 리터럴 대신 열거형으로 정의"""
    SUN_MASS = "sun_mass"
    EARTH_MASS = "earth_mass"
    BLACKHOLE = "blackhole"
    SIRIUS = "sirius"
    EARTH_DISTANCE = "earth_distance"
    EARTH_ROTATION = "earth_rotation"
    SOLAR_LUMINOSITY = "solar_luminosity"
    EARTH_ALBEDO = "earth_albedo"
    ATMOSPHERE_LOSS = "atmosphere_loss"
    MAGNETIC_FIELD = "magnetic_field"

# ============================================================================
# 1. 행성 데이터 & 클래스
# ============================================================================

@dataclass
class Planet:
    """행성 기본 정보 및 계산"""
    name: str
    mass: float
    radius: float
    orbit_r: float
    temp_k: float

    def orbital_period(self, sun_mass_factor: float = 1.0) -> float:
        """케플러 제3법칙"""
        return math.sqrt(self.orbit_r**3 / sun_mass_factor)

    def surface_gravity(self, mass_factor: float = 1.0) -> float:
        """표면 중력"""
        return (self.mass * mass_factor) / (self.radius**2)

    def escape_velocity(self, mass_factor: float = 1.0) -> float:
        """탈출속도"""
        return math.sqrt(2 * self.mass * mass_factor / self.radius)


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

    @staticmethod
    def _validate_change(percent_change: float) -> None:
        if not math.isfinite(percent_change) or percent_change <= -100:
            raise ValueError("질량 변화율은 유한한 값이며 -100%보다 커야 합니다.")

    @staticmethod
    def _calculate_earth_temperature(
        luminosity_ratio: float = 1.0,
        albedo: float = 0.306,
        distance_au: float = 1.0,
        atmosphere_fraction: float = 1.0,
    ) -> float:
        """지표 온도 계산 (통일된 공식)

        T_eq = 278.5 * (L_ratio ** 0.25) * ((1 - albedo) ** 0.25) / sqrt(d_AU)
        T_surface = T_eq + greenhouse_offset * atmosphere_fraction

        Args:
            luminosity_ratio: 태양 광도 배율 (현재 = 1.0)
            albedo: 지표 반사율 (현재 = 0.306)
            distance_au: 태양-지구 거리 AU (현재 = 1.0)
            atmosphere_fraction: 대기 잔존 비율 (현재 = 1.0, 완전 소실 = 0.0)

        Returns:
            T_surface (K)
        """
        CONST_278_5 = 278.5
        GREENHOUSE_OFFSET = 33.9  # 현재 지구를 288K에 보정

        t_eq = (
            CONST_278_5
            * (luminosity_ratio ** 0.25)
            * ((1.0 - albedo) ** 0.25)
            / math.sqrt(distance_au)
        )
        t_surface = t_eq + GREENHOUSE_OFFSET * atmosphere_fraction
        return t_surface

    def scenario_sun_mass_change(self, percent_change: float) -> Dict[str, Any]:
        """태양 질량 변화

        두 가지 모델 제공:
        - A (원궤도 유지): 기존 케플러 3법칙, 태양이 원래부터 그 질량
        - B (갑작스러운 변화): 태양이 순간 질량 변화, 지구 속도 고정, 궤도가 타원화
        """
        self._validate_change(percent_change)
        factor = 1.0 + percent_change / 100.0
        results = {}

        for name, planet in self.planets.items():
            period_before = planet.orbital_period(1.0)
            period_after = planet.orbital_period(factor)

            results[name] = {
                'name': planet.name,
                'orbital_period_change_pct': (
                    (period_after - period_before) / period_before
                ) * 100,
                'period_hours_change': (period_after - period_before) * 365 * 24,
                'orbit_r': planet.orbit_r,
            }

        # 케플러 3법칙: T ∝ M^(-0.5) → 주기 배율 = 1 / √factor
        period_ratio = 1.0 / math.sqrt(factor)

        # 모델 B: 태양이 갑자기 질량 변화할 때 (지구 속도 고정 가정)
        # E = ½v² - GM'/r = GM/(2r) - GM'/r (v² = GM/r)
        # 탈출 조건: E ≥ 0 → M' ≤ M/2
        earth_orbit_model_b = self._earth_orbit_sudden_change(factor)

        return {
            'scenario': f'태양 질량 {percent_change:+.1f}%',
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': percent_change,
            'period_ratio': period_ratio,  # 애니메이션용 (모델 A)
            'orbit_model_a': {
                'description': '원궤도 유지 (태양이 원래부터 이 질량)',
                'period_ratio': period_ratio,
            },
            'orbit_model_b': earth_orbit_model_b,  # 모델 B
            'results': results,
        }

    @staticmethod
    def _earth_orbit_sudden_change(mu: float) -> Dict[str, Any]:
        """태양 질량이 순간 변화할 때 지구 궤도의 변화.

        Args:
            mu: 변한 뒤 태양 질량 / 원래 태양 질량

        Returns:
            탈출 여부, 새 궤도 특성 (장반경 비, 이심률, 주기 비)
        """
        if mu <= 0.5:
            return {
                'description': '갑작스러운 변화 (지구 속도 고정)',
                'escape': True,
                'escape_velocity_reached': f'μ={mu:.3f} ≤ 0.5일 때 탈출',
                'note': '지구의 운동에너지가 증가한 중력장을 벗어남'
            }

        # 새 궤도 특성 계산
        a_ratio = mu / (2 * mu - 1)  # 새 궤도 장반경 / 현재 궤도
        e = abs(mu - 1) / mu  # 새 궤도 이심률
        period_ratio = a_ratio**1.5 / math.sqrt(mu)  # 새 공전주기 / 현재 주기

        return {
            'description': '갑작스러운 변화 (지구 속도 고정)',
            'escape': False,
            'a_ratio': a_ratio,
            'eccentricity': e,
            'period_ratio': period_ratio,
            'note': f'μ={mu:.3f}일 때 새 장반경={a_ratio:.3f}배, 이심률={e:.3f}'
        }

    def scenario_earth_mass_change(self, percent_change: float) -> Dict[str, Any]:
        """지구 질량 변화"""
        self._validate_change(percent_change)
        factor = 1.0 + percent_change / 100.0
        earth = self.planets['Earth']

        g_before = earth.surface_gravity(1.0)
        g_after = earth.surface_gravity(factor)

        return {
            'scenario': f'지구 질량 {percent_change:+.1f}%',
            'type': ScenarioType.EARTH_MASS.value,
            'percent_change': percent_change,
            'results': {
                'surface_gravity_change_pct': ((g_after - g_before) / g_before) * 100,
                'surface_gravity_new': g_after,
            },
        }

    def scenario_blackhole_nearby(
        self, mass_solar: float = 10.0, distance_au: float = 1.0
    ) -> Dict[str, Any]:
        """항성질량 블랙홀 출현 시 중력·조석력의 상대값을 계산한다.

        중력은 M/r², 조석력은 M/r³에 비례한다. 비교 기준은 태양이
        1 AU 거리에 있을 때이며, 1 AU에서는 지구가 사건지평선이나
        로슈 한계 안에 들어가지 않으므로 '즉시 찢김'으로 해석하지 않는다.
        """
        if not math.isfinite(mass_solar) or mass_solar <= 0:
            raise ValueError("블랙홀 질량은 0보다 큰 유한한 값이어야 합니다.")
        if not math.isfinite(distance_au) or distance_au <= 0:
            raise ValueError("블랙홀 거리는 0보다 큰 유한한 값이어야 합니다.")

        gravity_ratio = mass_solar / distance_au**2
        tidal_ratio = mass_solar / distance_au**3
        schwarzschild_radius_km = 2.953 * mass_solar

        return {
            'scenario': f'{mass_solar:g} 태양질량 블랙홀 {distance_au:g} AU 출현',
            'type': ScenarioType.BLACKHOLE.value,
            'threat': 100,
            'assumptions': {
                'mass_solar': mass_solar,
                'distance_au': distance_au,
                'appears_suddenly': True,
            },
            'results': {
                'gravity_ratio_to_sun_at_1au': gravity_ratio,
                'tidal_ratio_to_sun_at_1au': tidal_ratio,
                'schwarzschild_radius_km': schwarzschild_radius_km,
                'direct_spaghettification_at_distance': False,
                'primary_risk': '태양계 궤도와 중력 균형의 심각한 붕괴',
            },
            'limitations': '실제 결과는 블랙홀의 접근 방향·속도와 다른 천체의 위치에 따라 달라짐',
        }

    def scenario_sirius_nearby(
        self, distance_au: float = 1.0, mass_solar: float = 2.063,
        luminosity_solar: float = 24.7,
    ) -> Dict[str, Any]:
        """시리우스 A가 가까이 왔을 때 중력과 복사량을 단순 비교한다."""
        if not math.isfinite(distance_au) or distance_au <= 0:
            raise ValueError("시리우스 거리는 0보다 큰 유한한 값이어야 합니다.")
        if mass_solar <= 0 or luminosity_solar <= 0:
            raise ValueError("시리우스의 질량과 광도는 0보다 커야 합니다.")

        gravity_ratio = mass_solar / distance_au**2
        flux_sirius = luminosity_solar / distance_au**2
        # 복사 평형 온도는 입사 에너지의 4제곱근에 비례하는 단순 모델이다.
        # 태양과 시리우스의 합산 복사를 고려 (태양 복사 기본값 1.0 + 시리우스)
        total_flux = 1.0 + flux_sirius  # ← 태양의 몫 1.0을 반드시 더한다
        estimated_temp_k = 288 * total_flux**0.25

        return {
            'scenario': f'시리우스 A {distance_au:g} AU 출현',
            'type': ScenarioType.SIRIUS.value,
            'threat': 95,
            'assumptions': {
                'distance_au': distance_au,
                'mass_solar': mass_solar,
                'luminosity_solar': luminosity_solar,
            },
            'results': {
                'gravity_ratio_to_sun_at_1au': gravity_ratio,
                'radiation_ratio_to_earth': flux_sirius,
                'estimated_earth_temp_k': estimated_temp_k,
                'estimated_earth_temp_c': estimated_temp_k - 273.15,
                'primary_risk': '극심한 가열과 다중 항성계의 궤도 불안정',
            },
            'limitations': '대기·해양 순환과 온실효과를 생략한 복사 평형 근사치',
        }

    def scenario_earth_distance(self, distance_change_pct: float = 0.0) -> Dict[str, Any]:
        """지구 궤도 반지름 변화에 따른 복사 에너지 변화."""
        self._validate_change(distance_change_pct)
        factor = 1.0 + distance_change_pct / 100.0
        # 거리 변화: d' = d * (1 + pct/100)
        new_distance_au = factor
        # 복사는 거리의 제곱에 반비례
        radiation_ratio = 1.0 / factor**2
        estimated_temp_k = self._calculate_earth_temperature(
            luminosity_ratio=1.0,
            albedo=0.306,
            distance_au=new_distance_au,
            atmosphere_fraction=1.0,
        )
        return {
            'scenario': f'지구 궤도 {distance_change_pct:+.1f}%',
            'type': ScenarioType.EARTH_DISTANCE.value,
            'percent_change': distance_change_pct,
            'results': {
                'radiation_ratio_to_earth': radiation_ratio,
                'estimated_earth_temp_c': estimated_temp_k - 273.15,
            },
        }

    def scenario_earth_rotation(self, hours_per_day: float = 24.0) -> Dict[str, Any]:
        """지구 자전 속도 변화 (하루의 길이)."""
        if not math.isfinite(hours_per_day) or hours_per_day <= 0:
            raise ValueError("하루 길이는 0보다 큰 값이어야 합니다.")
        change_pct = ((hours_per_day - 24.0) / 24.0) * 100

        # 유효중력 계산 (원심가속도 포함)
        # g_eff = g - ω²R, ω = 2π/T, R = 지구반지름
        hours_to_seconds = hours_per_day * 3600.0
        omega = 2.0 * math.pi / hours_to_seconds
        earth_radius_m = 6.371e6  # 지구반지름 (m)
        centrifugal_accel = omega**2 * earth_radius_m
        surface_gravity = 9.81  # m/s²
        effective_gravity = surface_gravity - centrifugal_accel

        # 정확한 임계값: T_crit = 2π√(R/g) ≈ 1.40652시간
        # 유효중력이 0 이하면 붕괴 (지구 형태 유지 불가)
        is_collapse_condition = effective_gravity <= 0.0

        return {
            'scenario': f'하루 길이 {hours_per_day:.1f}시간',
            'type': ScenarioType.EARTH_ROTATION.value,
            'hours_per_day': hours_per_day,
            'results': {
                'rotation_change_pct': change_pct,
                'day_length_change_hours': hours_per_day - 24.0,
                'effective_gravity_ms2': effective_gravity,
                'centrifugal_accel_ms2': centrifugal_accel,
                'is_collapse_condition': is_collapse_condition,
            },
        }

    def scenario_solar_luminosity(self, luminosity_change_pct: float = 0.0) -> Dict[str, Any]:
        """태양 광도 변화에 따른 지표 온도 변화."""
        self._validate_change(luminosity_change_pct)
        factor = 1.0 + luminosity_change_pct / 100.0
        estimated_temp_k = self._calculate_earth_temperature(
            luminosity_ratio=factor,
            albedo=0.306,
            distance_au=1.0,
            atmosphere_fraction=1.0,
        )
        return {
            'scenario': f'태양 광도 {luminosity_change_pct:+.1f}%',
            'type': ScenarioType.SOLAR_LUMINOSITY.value,
            'percent_change': luminosity_change_pct,
            'results': {
                'luminosity_ratio': factor,
                'estimated_earth_temp_c': estimated_temp_k - 273.15,
            },
        }

    def scenario_earth_albedo(self, albedo_change_pct: float = 0.0) -> Dict[str, Any]:
        """지표 반사율 변화 (빙하기-온실 사이클)."""
        if not math.isfinite(albedo_change_pct) or albedo_change_pct < -100:
            raise ValueError("반사율 변화는 유효한 값이어야 합니다.")
        # 현재 지구 반사율 = 0.306
        current_albedo = 0.306
        new_albedo = max(0.0, min(1.0, current_albedo * (1.0 + albedo_change_pct / 100.0)))
        estimated_temp_k = self._calculate_earth_temperature(
            luminosity_ratio=1.0,
            albedo=new_albedo,
            distance_au=1.0,
            atmosphere_fraction=1.0,
        )
        absorbed_ratio = 1.0 - new_albedo
        return {
            'scenario': f'지표 반사율 {albedo_change_pct:+.1f}%',
            'type': ScenarioType.EARTH_ALBEDO.value,
            'albedo_change_pct': albedo_change_pct,
            'results': {
                'albedo_value': new_albedo,
                'absorbed_energy_ratio': absorbed_ratio,
                'estimated_earth_temp_c': estimated_temp_k - 273.15,
            },
        }

    def scenario_atmosphere_loss(self, atmosphere_remaining_pct: float = 100.0) -> Dict[str, Any]:
        """대기 손실에 따른 환경 변화."""
        if not math.isfinite(atmosphere_remaining_pct) or atmosphere_remaining_pct < 0 or atmosphere_remaining_pct > 100:
            raise ValueError("대기 잔존율은 0~100 사이여야 합니다.")
        # 대기 잔존율 (0~1)
        atmosphere_fraction = atmosphere_remaining_pct / 100.0
        # 통일된 온도 공식 사용
        estimated_temp_k = self._calculate_earth_temperature(
            luminosity_ratio=1.0,
            albedo=0.306,
            distance_au=1.0,
            atmosphere_fraction=atmosphere_fraction,
        )
        # 온도 감소량 계산 (대기 100% 기준 - 현재)
        temp_at_full_atm = self._calculate_earth_temperature(
            luminosity_ratio=1.0,
            albedo=0.306,
            distance_au=1.0,
            atmosphere_fraction=1.0,
        )
        temp_reduction = temp_at_full_atm - estimated_temp_k
        return {
            'scenario': f'대기 {atmosphere_remaining_pct:.0f}% 잔존',
            'type': ScenarioType.ATMOSPHERE_LOSS.value,
            'atmosphere_remaining_pct': atmosphere_remaining_pct,
            'results': {
                'atmosphere_factor': atmosphere_fraction,
                'temp_reduction_k': temp_reduction,
                'estimated_earth_temp_c': estimated_temp_k - 273.15,
                'uv_exposure_increase_pct': (1.0 - atmosphere_fraction) * 100,
            },
        }

    def scenario_magnetic_field(self, field_strength_pct: float = 100.0) -> Dict[str, Any]:
        """지구 자기장 강도 변화의 영향."""
        if not math.isfinite(field_strength_pct) or field_strength_pct < 0:
            raise ValueError("자기장 강도는 0 이상이어야 합니다.")
        factor = field_strength_pct / 100.0
        # 자기장이 약해지면 태양풍과 우주선 증가
        solar_wind_ratio = 1.0 + (1.0 - factor) * 2.0  # 0% 필드면 3배 태양풍
        return {
            'scenario': f'자기장 강도 {field_strength_pct:.0f}%',
            'type': ScenarioType.MAGNETIC_FIELD.value,
            'field_strength_pct': field_strength_pct,
            'results': {
                'field_factor': factor,
                'solar_wind_increase': solar_wind_ratio - 1.0,
                'primary_risk': '우주선 증가, 대기 손실 가속' if factor < 0.5 else '정상 범위',
            },
        }


