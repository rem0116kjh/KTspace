"""
태양계 "What If" 시뮬레이션 - OpenAI API 해석 모듈
중·고등학교 대회용 (심화 버전, 더 자연스러운 설명)

OpenAI API key는 환경변수로 관리 (안전)

실행:
  cp .env.example .env
  # .env 파일에 새로 발급한 키 입력
  pip install -r requirements.txt
  python3 solar_system_sim_v2_openai.py
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 로컬 개발에서는 .env를 읽고, 배포 환경에서는 시스템 환경변수를 사용한다.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI 라이브러리 (선택적)
try:
    from openai import OpenAI
    from openai import APIError, APIConnectionError, RateLimitError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    APIError = Exception  # 타입 체크용 Fallback
    APIConnectionError = Exception
    RateLimitError = Exception

# 로거 설정
logger = logging.getLogger(__name__)


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
        return np.sqrt(self.orbit_r**3 / sun_mass_factor)

    def surface_gravity(self, mass_factor: float = 1.0) -> float:
        """표면 중력"""
        return (self.mass * mass_factor) / (self.radius**2)

    def escape_velocity(self, mass_factor: float = 1.0) -> float:
        """탈출속도"""
        return np.sqrt(2 * self.mass * mass_factor / self.radius)


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
        if not np.isfinite(percent_change) or percent_change <= -100:
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
            / np.sqrt(distance_au)
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
        period_ratio = 1.0 / np.sqrt(factor)

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
        period_ratio = a_ratio**1.5 / np.sqrt(mu)  # 새 공전주기 / 현재 주기

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
        if not np.isfinite(mass_solar) or mass_solar <= 0:
            raise ValueError("블랙홀 질량은 0보다 큰 유한한 값이어야 합니다.")
        if not np.isfinite(distance_au) or distance_au <= 0:
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
        if not np.isfinite(distance_au) or distance_au <= 0:
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
        if not np.isfinite(hours_per_day) or hours_per_day <= 0:
            raise ValueError("하루 길이는 0보다 큰 값이어야 합니다.")
        change_pct = ((hours_per_day - 24.0) / 24.0) * 100

        # 유효중력 계산 (원심가속도 포함)
        # g_eff = g - ω²R, ω = 2π/T, R = 지구반지름
        hours_to_seconds = hours_per_day * 3600.0
        omega = 2.0 * np.pi / hours_to_seconds
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
        if not np.isfinite(albedo_change_pct) or albedo_change_pct < -100:
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
        if not np.isfinite(atmosphere_remaining_pct) or atmosphere_remaining_pct < 0 or atmosphere_remaining_pct > 100:
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
        if not np.isfinite(field_strength_pct) or field_strength_pct < 0:
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


# ============================================================================
# 3. OpenAI API 해석 모듈
# ============================================================================


class AIInterpreter:
    """OpenAI API를 사용한 자동 해석"""

    def __init__(self) -> None:
        """환경변수에서 API key 읽음 (권장)"""
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client: Optional[OpenAI] = None

        if not self.api_key:
            logger.info("OPENAI_API_KEY가 없어 기본 해설 모드를 사용함")
            return

        if not HAS_OPENAI:
            logger.error("openai 라이브러리가 설치되지 않음. pip install openai 실행 필요")
            return

        try:
            self.client = OpenAI(api_key=self.api_key, timeout=30.0)
        except Exception as e:
            logger.exception("OpenAI 클라이언트 초기화 실패")

    def interpret_scenario(
        self, scenario: Dict[str, Any], max_tokens: int = 400
    ) -> Optional[str]:
        """
        OpenAI에 시뮬레이션 결과 해석 요청

        Args:
            scenario: 시뮬레이션 결과 딕셔너리
            max_tokens: 응답 최대 토큰 수 (1~4000, 기본값 400)

        Returns:
            AI 해석 텍스트 또는 None (실패 시)
        """
        # 초기화 실패 확인
        if not self.client:
            logger.warning("OpenAI 클라이언트가 초기화되지 않음")
            return None

        # 입력 검증
        if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 4000):
            logger.error(f"유효하지 않은 max_tokens: {max_tokens}")
            return None

        if not isinstance(scenario, dict) or 'type' not in scenario:
            logger.error("유효하지 않은 시나리오 형식")
            return None

        # 프롬프트 생성 (try 블록 내부로 이동)
        try:
            prompt = self._build_prompt(scenario)
        except ValueError as e:
            logger.error(f"프롬프트 생성 실패: {e}")
            return None

        try:
            # OpenAI API 호출 (chat.completions.create 사용)
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 중학교 과학 교사입니다. "
                            "복잡한 물리 개념을 중학생(13-15세)이 이해할 수 있게 설명해주세요. "
                            "어려운 용어는 피하고, 일상적인 예시를 사용하세요. "
                            "제공된 계산값만 사용하고 새로운 수치를 지어내지 마세요. "
                            "계산 결과와 단순 모델의 한계를 구분해서 말하세요. "
                            "3-4문장으로 간결하게 설명하세요."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            # 응답 검증 및 추출
            if not response.choices or not response.choices[0].message.content:
                logger.warning(
                    f"빈 응답 또는 콘텐츠 필터 거부 (type={scenario.get('type')})"
                )
                return None

            return response.choices[0].message.content

        except RateLimitError:
            logger.warning("API 속도 제한 도달 - 나중에 재시도 필요")
            return None
        except APIConnectionError as e:
            logger.error(f"API 연결 오류: {e}")
            return None
        except APIError as e:
            logger.error(f"API 오류 (type={scenario.get('type')}): {e}")
            return None
        except Exception as e:
            logger.exception(f"예상치 못한 오류 (type={scenario.get('type')})")
            return None

    def _build_prompt(self, scenario: Dict[str, Any]) -> str:
        """
        시나리오를 프롬프트로 변환

        Args:
            scenario: 시뮬레이션 결과 딕셔너리

        Returns:
            LLM으로 전송할 프롬프트 문자열

        Raises:
            ValueError: 알 수 없는 시나리오 타입
        """
        s_type = scenario.get("type")

        if s_type == ScenarioType.SUN_MASS.value:
            change = scenario.get("percent_change", 0)
            earth_data = scenario.get("results", {}).get("Earth", {})
            period_change = earth_data.get("orbital_period_change_pct", 0)

            return (
                f"태양의 질량이 {change:+.1f}% 변했을 때, "
                f"지구의 공전 주기가 {period_change:.3f}% 변합니다. "
                f"이것이 지구 생명에 어떤 영향을 미칠까요? 중학생 수준으로."
            )

        elif s_type == ScenarioType.EARTH_MASS.value:
            change = scenario.get("percent_change", 0)
            g_change = scenario.get("results", {}).get(
                "surface_gravity_change_pct", 0
            )

            return (
                f"지구의 질량이 {change:+.1f}% 증가하면, "
                f"표면 중력이 {g_change:.2f}% 증가합니다. "
                f"생물에게 어떤 의미가 있을까요? 중학생 수준으로."
            )

        elif s_type == ScenarioType.BLACKHOLE.value:
            assumptions = scenario.get("assumptions", {})
            results = scenario.get("results", {})
            return (
                f"태양 질량의 {assumptions.get('mass_solar', 10):g}배인 블랙홀이 "
                f"지구에서 {assumptions.get('distance_au', 1):g} AU 거리에 갑자기 나타나는 "
                f"가상 상황입니다. 태양 1 AU 기준 중력은 "
                f"{results.get('gravity_ratio_to_sun_at_1au', 10):.1f}배, 조석력은 "
                f"{results.get('tidal_ratio_to_sun_at_1au', 10):.1f}배입니다. "
                "이 거리에서 지구가 즉시 스파게티화된다고 단정하지 말고, "
                "태양계 궤도 교란을 중심으로 중학생 수준에서 설명하세요."
            )

        elif s_type == ScenarioType.SIRIUS.value:
            assumptions = scenario.get("assumptions", {})
            results = scenario.get("results", {})
            return (
                f"질량이 태양의 {assumptions.get('mass_solar', 2.02):.2f}배, 광도가 "
                f"{assumptions.get('luminosity_solar', 25.4):.1f}배인 시리우스 A가 "
                f"{assumptions.get('distance_au', 1):g} AU 거리에 나타나는 가상 상황입니다. "
                f"지구가 받는 복사 에너지는 {results.get('radiation_ratio_to_earth', 25.4):.1f}배, "
                f"단순 추정 온도는 약 {results.get('estimated_earth_temp_c', 375):.0f}°C입니다. "
                "모델의 한계와 생명에 미칠 영향을 중학생 수준에서 설명하세요."
            )

        elif s_type == ScenarioType.EARTH_DISTANCE.value:
            results = scenario.get("results", {})
            change = scenario.get("percent_change", 0)
            direction = "먼" if change > 0 else "가까운"
            return (
                f"지구 궤도 반지름이 {abs(change):.1f}% {direction}쪽으로 변하면 "
                f"태양 복사는 {results.get('radiation_ratio_to_earth', 1):.4f}배가 됩니다. "
                f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
                "거리와 에너지의 관계를 중학생 수준에서 설명하세요."
            )

        elif s_type == ScenarioType.EARTH_ROTATION.value:
            hours = scenario.get("hours_per_day", 24)
            change = scenario.get("rotation_change_pct", 0)
            return (
                f"지구의 자전 속도가 변해 하루가 {hours:.1f}시간이 되었습니다. "
                f"변화는 {change:+.1f}%입니다. "
                "낮과 밤의 길이 변화가 생명에 미칠 영향을 중학생 수준에서 설명하세요."
            )

        elif s_type == ScenarioType.SOLAR_LUMINOSITY.value:
            results = scenario.get("results", {})
            change = scenario.get("percent_change", 0)
            return (
                f"태양 광도가 {change:+.1f}% 변했습니다. "
                f"지구 추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
                "태양 에너지의 작은 변화가 지구 기후에 미치는 영향을 설명하세요."
            )

        elif s_type == ScenarioType.EARTH_ALBEDO.value:
            results = scenario.get("results", {})
            change = scenario.get("albedo_change_pct", 0)
            new_albedo = results.get("albedo_value", 0.3)
            return (
                f"지표 반사율이 {change:+.1f}% 변해 {new_albedo:.3f}가 되었습니다. "
                f"지구 추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
                "반사율과 온도의 관계를 빙하기 사례로 설명하세요."
            )

        elif s_type == ScenarioType.ATMOSPHERE_LOSS.value:
            results = scenario.get("results", {})
            pct = scenario.get("atmosphere_remaining_pct", 100)
            return (
                f"지구 대기가 {pct:.0f}%만 남았습니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C, "
                f"우주선 노출은 {results.get('uv_exposure_increase_pct', 0):.0f}% 증가합니다. "
                "화성의 얇은 대기와 비교하며 대기 손실의 위험을 설명하세요."
            )

        elif s_type == ScenarioType.MAGNETIC_FIELD.value:
            results = scenario.get("results", {})
            pct = scenario.get("field_strength_pct", 100)
            return (
                f"지구 자기장이 {pct:.0f}% 강도입니다. "
                f"태양풍 영향은 {results.get('solar_wind_increase', 0):+.1f}배 증가합니다. "
                "약한 자기장이 대기 손실과 생명 보호에 미치는 장기적 영향을 설명하세요."
            )

        # 알 수 없는 타입은 예외 발생
        raise ValueError(f"알 수 없는 시나리오 타입: {s_type!r}")


def fallback_interpretation(scenario: Dict[str, Any]) -> str:
    """API를 사용할 수 없을 때 보여주는 검증 가능한 기본 해설."""
    s_type = scenario.get("type")

    if s_type == ScenarioType.SUN_MASS.value:
        change = scenario.get("percent_change", 0)
        earth = scenario.get("results", {}).get("Earth", {})
        period = earth.get("orbital_period_change_pct", 0)
        direction = "짧아집니다" if period < 0 else "길어집니다"

        model_b = scenario.get("orbit_model_b", {})
        if model_b.get("escape"):
            return (
                f"태양 질량이 {change:+.1f}% 변하면 태양의 중력이 달라집니다. "
                "만약 태양 질량이 갑자기 떨어진다면 지구는 탈출 속도에 도달해 영원히 떠나갑니다. "
                f"반면 서서히 변한다면 원궤도를 유지하며 새 주기로 공전합니다."
            )
        else:
            period_b = model_b.get("period_ratio", 1.0)
            return (
                f"태양 질량이 {change:+.1f}% 변하는 두 시나리오를 비교합니다. "
                f"① 서서히 변하면: 원궤도 유지, 주기 {abs(period):.1f}% {direction}. "
                f"② 갑자기 변하면: 궤도 타원화, 새 주기 {abs(period_b - 1.0) * 100:.1f}% {'길어짐' if period_b > 1.0 else '짧아짐'}. "
                "지구 생명은 느린 변화에 적응할 가능성이 더 높습니다."
            )

    if s_type == ScenarioType.EARTH_MASS.value:
        change = scenario.get("percent_change", 0)
        gravity = scenario.get("results", {}).get("surface_gravity_change_pct", 0)
        return (
            f"지구 질량이 {change:+.1f}% 변하면 표면 중력도 약 {gravity:+.2f}% 변합니다. "
            "질량이 커질수록 사람과 물체가 받는 무게가 늘고 대기를 붙잡는 힘도 강해집니다. "
            "다만 이 단순 모델은 지구 반지름 변화를 따로 계산하지 않습니다."
        )

    if s_type == ScenarioType.BLACKHOLE.value:
        assumptions = scenario.get("assumptions", {})
        results = scenario.get("results", {})
        return (
            f"태양 질량의 {assumptions.get('mass_solar', 10):g}배인 블랙홀이 "
            f"{assumptions.get('distance_au', 1):g} AU 거리에 갑자기 나타나는 가상 상황입니다. "
            f"이 위치에서 중력과 조석력은 태양 1 AU 기준 각각 약 "
            f"{results.get('gravity_ratio_to_sun_at_1au', 10):.1f}배와 "
            f"{results.get('tidal_ratio_to_sun_at_1au', 10):.1f}배입니다. "
            "지구가 그 자리에서 즉시 찢어진다기보다 기존 태양계 궤도와 중력 균형이 "
            "심각하게 무너지는 것이 핵심 위험입니다."
        )

    if s_type == ScenarioType.SIRIUS.value:
        results = scenario.get("results", {})
        return (
            f"시리우스 A가 1 AU 거리에 나타나면 지구가 받는 복사 에너지는 현재의 약 "
            f"{results.get('radiation_ratio_to_earth', 25.4):.1f}배가 됩니다. "
            f"대기와 해양을 생략한 단순 모델의 추정 온도는 약 "
            f"{results.get('estimated_earth_temp_c', 375):.0f}°C입니다. "
            "극심한 가열과 두 별의 중력이 만드는 궤도 불안정이 핵심 위험입니다."
        )

    if s_type == ScenarioType.EARTH_DISTANCE.value:
        results = scenario.get("results", {})
        change = scenario.get("percent_change", 0)
        direction = "먼" if change > 0 else "가까운"
        return (
            f"지구 궤도 반지름이 {abs(change):.1f}% {direction}쪽으로 변하면 "
            f"태양 복사 에너지는 {results.get('radiation_ratio_to_earth', 1):.4f}배가 됩니다. "
            f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
            "궤도 거리의 작은 변화도 장기적으로 생명에 큰 영향을 줄 수 있습니다."
        )

    if s_type == ScenarioType.EARTH_ROTATION.value:
        hours = scenario.get("hours_per_day", 24)
        results = scenario.get("results", {})
        # 붕괴 조건 확인: T_crit = 2π√(R/g) ≈ 1.407시간
        if results.get("is_collapse_condition"):
            g_eff = results.get("effective_gravity_ms2", 0)
            t_crit = 2.0 * np.pi * np.sqrt(6.371e6 / 9.81) / 3600.0  # 시간 단위
            return (
                f"하루가 {hours:.1f}시간이면 적도에서 원심력이 중력을 초과합니다. "
                f"유효중력이 {g_eff:.2f} m/s²(음수)가 되어 지구는 구형을 유지할 수 없습니다. "
                f"임계값({t_crit:.3f}시간)보다 짧으므로 생명 존재 불가능합니다."
            )
        else:
            return (
                f"하루가 {hours:.1f}시간으로 변하면 낮과 밤의 길이가 달라져 "
                "지표의 온도 변화가 커집니다. "
                f"짧은 하루는 더 빠른 냉각을, 긴 하루는 더 많은 가열을 의미합니다."
            )

    if s_type == ScenarioType.SOLAR_LUMINOSITY.value:
        results = scenario.get("results", {})
        change = scenario.get("percent_change", 0)
        return (
            f"태양 광도가 {change:+.1f}% 변하면 지구가 받는 에너지가 변합니다. "
            f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
            "광도의 작은 변화도 복사 평형에 큰 영향을 주어 기후를 급변시킬 수 있습니다."
        )

    if s_type == ScenarioType.EARTH_ALBEDO.value:
        results = scenario.get("results", {})
        change = scenario.get("albedo_change_pct", 0)
        direction = "증가" if change > 0 else "감소"
        return (
            f"지표 반사율이 {abs(change):.1f}% {direction}하면 흡수되는 에너지가 변합니다. "
            f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
            "빙하기와 온실 지구의 차이도 반사율 변화로 설명됩니다."
        )

    if s_type == ScenarioType.ATMOSPHERE_LOSS.value:
        results = scenario.get("results", {})
        pct = scenario.get("atmosphere_remaining_pct", 100)

        if pct >= 90:
            return (
                f"대기가 {pct:.0f}% 남으면 현재 지구와 비슷하게 온실효과가 유지됩니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 정상 범위입니다. "
                "생명이 번성할 수 있는 환경이 유지됩니다."
            )
        elif pct >= 30:
            return (
                f"대기가 {pct:.0f}% 남으면 온실효과가 약화되어 우주선 노출이 증가합니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 감소합니다. "
                "생명에 자외선 스트레스가 증가합니다."
            )
        else:  # pct < 30
            return (
                f"대기가 {pct:.0f}% 남으면 온실효과가 거의 사라지고 우주선이 직접 투과합니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 급락합니다. "
                "화성처럼 얇은 대기를 가지게 되어 생명 환경이 급격히 악화됩니다."
            )

    if s_type == ScenarioType.MAGNETIC_FIELD.value:
        results = scenario.get("results", {})
        pct = scenario.get("field_strength_pct", 100)
        solar_wind_inc = results.get('solar_wind_increase', 0)

        if pct >= 90:
            subtitle = "정상적인 자기장이 태양풍을 차단하고 있습니다"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양풍 차단이 효과적이므로 대기 손실이 최소입니다. "
                f"태양풍 영향은 {solar_wind_inc:+.1f}배에 불과합니다. "
                "지구의 대기와 생명이 우주 방사선으로부터 보호됩니다."
            )
        elif pct >= 50:
            subtitle = "약화된 자기장이 부분적으로만 보호합니다"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양풍 차단이 약해져 대기 손실이 증가합니다. "
                f"태양풍 영향은 {solar_wind_inc:+.1f}배 증가합니다. "
                "우주선 노출도 증가하여 생명에 스트레스를 줍니다."
            )
        else:  # pct < 50
            subtitle = "거의 없는 자기장은 태양풍을 막지 못합니다"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양풍 차단이 거의 불가능하고 대기 손실이 급속합니다. "
                f"태양풍 영향은 {solar_wind_inc:+.1f}배 증가합니다. "
                "행성의 대기가 우주로 빠져나가 생명 환경이 급격히 악화됩니다."
            )

        return f"{subtitle}\n\n{explanation}"

    return "이 시나리오는 아직 기본 해설이 준비되지 않았습니다."


# ============================================================================
# 4. 메인 실행
# ============================================================================


def main() -> None:
    """메인 실행 함수"""
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    print("\n" + "=" * 80)
    print("🚀 태양계 'What If' 시뮬레이션 - OpenAI API 해석 버전")
    print("   중·고등학교 AI·데이터 분석 대회 (심화 버전)")
    print("=" * 80)

    if not HAS_OPENAI:
        print("\n❌ openai 라이브러리 없음")
        print("   설치: pip install openai")
        return

    # 엔진 & AI 초기화
    engine = SimulationEngine(PLANETS)
    ai = AIInterpreter()

    if ai.client:
        print(f"\n✅ AI 해설 사용 가능 (모델: {ai.model})\n")
    else:
        print("\nℹ️  API 키가 없어 기본 해설 모드로 실행합니다.")
        print("   AI 해설을 사용하려면 .env 파일에 새 OPENAI_API_KEY를 설정하세요.\n")

    # 시나리오 목록
    scenarios = [
        engine.scenario_sun_mass_change(1.0),
        engine.scenario_sun_mass_change(-1.0),
        engine.scenario_earth_mass_change(1.0),
        engine.scenario_earth_mass_change(-1.0),
        engine.scenario_blackhole_nearby(),
        engine.scenario_sirius_nearby(),
    ]

    # 각 시나리오 처리
    for i, scenario in enumerate(scenarios, 1):
        print(f"{'=' * 80}")
        print(f"{i}. 📊 {scenario['scenario']}")
        print(f"{'=' * 80}")

        # 시뮬레이션 데이터 출력
        s_type = scenario.get("type")
        if s_type == ScenarioType.SUN_MASS.value:
            earth_data = scenario["results"]["Earth"]
            print(
                f"\n📈 지구의 공전 주기 변화: "
                f"{earth_data['orbital_period_change_pct']:.3f}%"
            )
            print(f"   시간 변화: {earth_data['period_hours_change']:.1f}시간")

        elif s_type == ScenarioType.EARTH_MASS.value:
            print(
                f"\n⚖️  표면 중력 변화: "
                f"{scenario['results']['surface_gravity_change_pct']:+.2f}%"
            )

        elif s_type in [ScenarioType.BLACKHOLE.value, ScenarioType.SIRIUS.value]:
            print(f"\n⚠️  위협 수준: {scenario['threat']}/100")
            if s_type == ScenarioType.BLACKHOLE.value:
                data = scenario["results"]
                print(f"   태양 1AU 대비 중력: {data['gravity_ratio_to_sun_at_1au']:.1f}배")
                print(f"   태양 1AU 대비 조석력: {data['tidal_ratio_to_sun_at_1au']:.1f}배")
            else:
                data = scenario["results"]
                print(f"   지구가 받는 복사 에너지: {data['radiation_ratio_to_earth']:.1f}배")
                print(f"   단순 추정 온도: {data['estimated_earth_temp_c']:.0f}°C")

        # OpenAI로 자동 해석
        interpretation = ai.interpret_scenario(scenario) if ai.client else None
        if interpretation:
            print(f"\n💡 AI 해설 ({ai.model}):")
            print(f"\n{interpretation}\n")
        else:
            print("\n💡 기본 해설:")
            print(f"\n{fallback_interpretation(scenario)}\n")

    # 결론
    print("\n" + "=" * 80)
    print("✅ 시뮬레이션 & 해설 완료!")
    print("=" * 80)
    print("\n💡 이 해석들을 PPT 슬라이드에 추가하면,")
    print("   발표의 설득력이 훨씬 높아집니다!")


if __name__ == '__main__':
    main()
