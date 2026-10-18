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


# Keep the public imports used by the classic lab and existing integrations.
from simulation_engine import Planet, PLANETS, ScenarioType, SimulationEngine


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
            f"이 위치에서 잡아당기는 힘은 태양 1 AU 기준 약 "
            f"{results.get('gravity_ratio_to_sun_at_1au', 10):.1f}배이고, "
            f"지구를 늘어뜨리는 힘은 약 {results.get('tidal_ratio_to_sun_at_1au', 10):.1f}배입니다. "
            "지구가 즉시 찢어진다기보다 태양계의 궤도와 중력 균형이 "
            "심각하게 무너져 생명이 살 수 없게 되는 것이 가장 큰 위험입니다."
        )

    if s_type == ScenarioType.SIRIUS.value:
        results = scenario.get("results", {})
        return (
            f"시리우스 A가 1 AU 거리에 나타나면 지구가 받는 열은 현재의 약 "
            f"{results.get('radiation_ratio_to_earth', 25.4):.1f}배가 됩니다. "
            f"대기와 해양을 생략한 단순 모델의 추정 온도는 약 "
            f"{results.get('estimated_earth_temp_c', 375):.0f}°C입니다. "
            "극심한 가열과 두 별의 잡아당기는 힘이 지구 궤도를 흔들어 생명이 살 수 없게 되는 것이 핵심 위험입니다."
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
                f"하루가 {hours:.1f}시간이면 회전이 너무 빨라서 밖으로 튕겨나가는 힘이 중력을 이기게 됩니다. "
                f"무거워지는 힘이 사라져 지구는 동그란 모양을 유지할 수 없습니다. "
                f"약 {t_crit:.3f}시간보다 짧으면 생명이 살 수 없습니다."
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
            f"태양이 {change:+.1f}% 더 밝아지면 지구가 받는 열의 양이 변합니다. "
            f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
            "태양 밝기의 작은 변화도 지구가 받는 열의 균형을 깨뜨려 기후를 급변시킬 수 있습니다."
        )

    if s_type == ScenarioType.EARTH_ALBEDO.value:
        results = scenario.get("results", {})
        change = scenario.get("albedo_change_pct", 0)
        direction = "증가" if change > 0 else "감소"
        return (
            f"지표가 햇빛을 반사하는 양이 {abs(change):.1f}% {direction}하면 지구가 흡수하는 열의 양이 변합니다. "
            f"추정 온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C입니다. "
            "얼음이 많아지면(반사율 ↑) 춥고, 얼음이 녹으면(반사율 ↓) 더워지는 이유도 이것입니다."
        )

    if s_type == ScenarioType.ATMOSPHERE_LOSS.value:
        results = scenario.get("results", {})
        pct = scenario.get("atmosphere_remaining_pct", 100)

        if pct >= 90:
            return (
                f"대기가 {pct:.0f}% 남으면 현재 지구처럼 대기가 열을 잡아줍니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 정상 범위입니다. "
                "생명이 번성할 수 있는 환경이 유지됩니다."
            )
        elif pct >= 30:
            return (
                f"대기가 {pct:.0f}% 남으면 대기가 열을 잡아주는 능력이 약해져 우주의 나쁜 방사선이 더 들어옵니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 감소합니다. "
                "생명이 자외선 피해를 더 많이 입게 됩니다."
            )
        else:  # pct < 30
            return (
                f"대기가 {pct:.0f}% 남으면 대기가 거의 없어져 우주의 나쁜 방사선이 그대로 들어옵니다. "
                f"온도는 약 {results.get('estimated_earth_temp_c', 15):.0f}°C로 급락합니다. "
                "화성처럼 얇은 대기가 되어 생명이 살 수 없는 환경이 됩니다."
            )

    if s_type == ScenarioType.MAGNETIC_FIELD.value:
        results = scenario.get("results", {})
        pct = scenario.get("field_strength_pct", 100)
        solar_wind_inc = results.get('solar_wind_increase', 0)

        if pct >= 90:
            subtitle = "지구의 자기장이 우주의 위험한 에너지를 잘 막고 있어요"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양에서 오는 위험한 에너지를 잘 막아줍니다. "
                f"위험한 에너지의 영향은 {solar_wind_inc:+.1f}배 정도입니다. "
                "지구의 공기와 생명이 우주의 나쁜 방사선으로부터 보호받습니다."
            )
        elif pct >= 50:
            subtitle = "자기장이 약해져서 우주의 위험한 에너지가 더 들어와요"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양풍을 완벽하게 막지 못해 더 많은 위험한 에너지가 들어옵니다. "
                f"위험한 에너지의 영향은 {solar_wind_inc:+.1f}배 증가합니다. "
                "우주의 나쁜 방사선이 더 많이 들어와 생명이 스트레스를 받게 됩니다."
            )
        else:  # pct < 50
            subtitle = "자기장이 거의 없어서 우주의 위험한 에너지가 그대로 들어와요"
            explanation = (
                f"자기장이 {pct:.0f}% 강도면 태양풍을 거의 막지 못해 위험한 에너지가 계속 들어옵니다. "
                f"위험한 에너지의 영향은 {solar_wind_inc:+.1f}배 증가합니다. "
                "지구의 공기가 우주로 날아가면서 생명이 살 수 없는 환경이 되어갑니다."
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
