"""
pytest 테스트 - solar_system_sim_v2_openai.py

Mock을 사용하여 실제 API 호출 없이 검증
테스트 범위: AIInterpreter 클래스 (보안, 예외 처리, 입력 검증)
"""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from solar_system_sim_v2_openai import (
    AIInterpreter,
    Planet,
    ScenarioType,
    SimulationEngine,
)


# ============================================================================
# 1. 단위 테스트: Planet 클래스
# ============================================================================


class TestPlanet:
    """Planet 클래스 검증"""

    def test_planet_orbital_period_calculation(self):
        """케플러 제3법칙 계산 검증"""
        earth = Planet('지구', 1.0, 1.0, 1.0, 288)
        period_1x = earth.orbital_period(1.0)
        period_2x = earth.orbital_period(2.0)

        # 태양 질량이 2배면 공전 주기는 약 0.707배 (sqrt(2^-1))
        expected_ratio = 1 / (2 ** 0.5)
        actual_ratio = period_2x / period_1x
        assert abs(actual_ratio - expected_ratio) < 0.01

    def test_planet_surface_gravity(self):
        """표면 중력 계산 검증"""
        earth = Planet('지구', 1.0, 1.0, 1.0, 288)
        g_1x = earth.surface_gravity(1.0)
        g_2x = earth.surface_gravity(2.0)

        # 질량이 2배면 중력도 약 2배
        assert abs(g_2x / g_1x - 2.0) < 0.01


# ============================================================================
# 2. 단위 테스트: SimulationEngine 클래스
# ============================================================================


class TestSimulationEngine:
    """SimulationEngine 클래스 검증"""

    @pytest.fixture
    def planets(self):
        """테스트용 행성 데이터"""
        return {
            'Earth': Planet('지구', 1.0, 1.0, 1.0, 288),
            'Mars': Planet('화성', 0.107, 0.532, 1.524, 210),
        }

    @pytest.fixture
    def engine(self, planets):
        """테스트용 시뮬레이션 엔진"""
        return SimulationEngine(planets)

    def test_scenario_sun_mass_change_returns_dict(self, engine):
        """태양 질량 변화 시나리오 반환 타입 검증"""
        result = engine.scenario_sun_mass_change(1.0)

        # 딕셔너리 구조 검증
        assert isinstance(result, dict)
        assert 'scenario' in result
        assert 'type' in result
        assert 'percent_change' in result
        assert 'results' in result

    def test_scenario_sun_mass_change_uses_enum(self, engine):
        """시나리오 타입이 ScenarioType enum 사용 검증"""
        result = engine.scenario_sun_mass_change(1.0)
        assert result['type'] == ScenarioType.SUN_MASS.value

    def test_scenario_earth_mass_change_uses_enum(self, engine):
        """지구 질량 변화 시나리오가 enum 사용 검증"""
        result = engine.scenario_earth_mass_change(1.0)
        assert result['type'] == ScenarioType.EARTH_MASS.value

    def test_scenario_blackhole_nearby_uses_enum(self, engine):
        """블랙홀 시나리오가 enum 사용 검증"""
        result = engine.scenario_blackhole_nearby()
        assert result['type'] == ScenarioType.BLACKHOLE.value

    def test_scenario_sirius_nearby_uses_enum(self, engine):
        """시리우스 시나리오가 enum 사용 검증"""
        result = engine.scenario_sirius_nearby()
        assert result['type'] == ScenarioType.SIRIUS.value

    def test_blackhole_scenario_uses_explicit_physics_assumptions(self, engine):
        """블랙홀 질량·거리와 중력/조석력 비율을 명시적으로 계산"""
        result = engine.scenario_blackhole_nearby(mass_solar=10, distance_au=1)
        assert result['assumptions']['mass_solar'] == 10
        assert result['results']['gravity_ratio_to_sun_at_1au'] == pytest.approx(10)
        assert result['results']['tidal_ratio_to_sun_at_1au'] == pytest.approx(10)
        assert result['results']['direct_spaghettification_at_distance'] is False

    def test_blackhole_force_obeys_distance_scaling(self, engine):
        """중력은 거리 제곱, 조석력은 거리 세제곱에 반비례"""
        result = engine.scenario_blackhole_nearby(mass_solar=10, distance_au=2)
        assert result['results']['gravity_ratio_to_sun_at_1au'] == pytest.approx(2.5)
        assert result['results']['tidal_ratio_to_sun_at_1au'] == pytest.approx(1.25)

    def test_sirius_scenario_calculates_radiation_equilibrium_temperature(self, engine):
        """복사량과 온도는 각각 거리 제곱/복사량 4제곱근 법칙을 사용"""
        result = engine.scenario_sirius_nearby(
            distance_au=1, mass_solar=2.02, luminosity_solar=25.4
        )
        assert result['results']['radiation_ratio_to_earth'] == pytest.approx(25.4)
        expected_kelvin = 288 * (25.4 ** 0.25)
        assert result['results']['estimated_earth_temp_k'] == pytest.approx(expected_kelvin)

    @pytest.mark.parametrize('invalid_change', [-100, -101, float('nan')])
    def test_invalid_mass_changes_are_rejected(self, engine, invalid_change):
        with pytest.raises(ValueError):
            engine.scenario_sun_mass_change(invalid_change)


# ============================================================================
# 3. 단위 테스트: AIInterpreter 클래스
# ============================================================================


class TestAIInterpreterInit:
    """AIInterpreter.__init__() 검증"""

    def test_init_no_api_key_returns_none_client(self):
        """API Key 없을 때 client가 None 검증"""
        with patch.dict(os.environ, {}, clear=True):
            ai = AIInterpreter()
            assert ai.client is None
            assert ai.api_key is None

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-12345'})
    @patch('solar_system_sim_v2_openai.OpenAI')
    def test_init_with_api_key_creates_client(self, mock_openai_class):
        """API Key 있을 때 client 생성 검증"""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        ai = AIInterpreter()

        # OpenAI 클라이언트가 생성되었는지 확인
        mock_openai_class.assert_called_once()
        assert ai.client is not None
        assert ai.api_key == 'test-key-12345'

    def test_init_sets_timeout(self):
        """OpenAI 클라이언트에 timeout 설정 검증"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('solar_system_sim_v2_openai.OpenAI') as mock_openai_class:
                AIInterpreter()
                # timeout=30.0이 전달되는지 확인
                call_kwargs = mock_openai_class.call_args[1]
                assert call_kwargs.get('timeout') == 30.0


class TestAIInterpreterInterpretScenario:
    """AIInterpreter.interpret_scenario() 검증"""

    @pytest.fixture
    def mock_client_ai(self):
        """Mock OpenAI 클라이언트와 AIInterpreter"""
        ai = AIInterpreter()
        ai.client = MagicMock()
        return ai

    def test_interpret_scenario_returns_none_when_no_client(self):
        """클라이언트 없을 때 None 반환 검증"""
        ai = AIInterpreter()
        ai.client = None

        scenario = {'type': ScenarioType.SUN_MASS.value, 'percent_change': 1.0}
        result = ai.interpret_scenario(scenario)

        assert result is None

    def test_interpret_scenario_validates_max_tokens(self, mock_client_ai):
        """max_tokens 검증 (1~4000) 검증"""
        scenario = {'type': ScenarioType.SUN_MASS.value, 'percent_change': 1.0}

        # 0은 유효하지 않음
        result = mock_client_ai.interpret_scenario(scenario, max_tokens=0)
        assert result is None

        # 4001은 유효하지 않음
        result = mock_client_ai.interpret_scenario(scenario, max_tokens=4001)
        assert result is None

        # 1은 유효함 (호출 진행)
        mock_client_ai.client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="테스트 응답"))]
        )
        result = mock_client_ai.interpret_scenario(scenario, max_tokens=1)
        assert result == "테스트 응답"

    def test_interpret_scenario_invalid_scenario_dict(self, mock_client_ai):
        """유효하지 않은 시나리오 딕셔너리 검증"""
        # 'type' 키 없음
        result = mock_client_ai.interpret_scenario({})
        assert result is None

        # 'type'이 None
        result = mock_client_ai.interpret_scenario({'type': None})
        assert result is None

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_invalid_scenario_type(
        self, mock_logger, mock_client_ai
    ):
        """알 수 없는 시나리오 타입 예외 처리 검증"""
        scenario = {'type': 'unknown_type'}
        result = mock_client_ai.interpret_scenario(scenario)

        # ValueError가 로깅되고 None 반환
        assert result is None
        mock_logger.error.assert_called()

    def test_interpret_scenario_successful_call(self, mock_client_ai):
        """성공적인 API 호출 검증"""
        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="AI 해석 결과"))
        ]
        mock_client_ai.client.chat.completions.create.return_value = mock_response

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # 반환 값 검증
        assert result == "AI 해석 결과"

        # API가 올바르게 호출되었는지 검증
        mock_client_ai.client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client_ai.client.chat.completions.create.call_args[1]
        assert call_kwargs['model'] == 'gpt-4o-mini'
        assert call_kwargs['max_tokens'] == 400
        assert len(call_kwargs['messages']) == 2
        assert call_kwargs['messages'][0]['role'] == 'system'
        assert call_kwargs['messages'][1]['role'] == 'user'

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_empty_choices(
        self, mock_logger, mock_client_ai
    ):
        """빈 choices 응답 처리 검증"""
        mock_response = MagicMock()
        mock_response.choices = []
        mock_client_ai.client.chat.completions.create.return_value = mock_response

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # 빈 응답은 None 반환
        assert result is None
        mock_logger.warning.assert_called()

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_rate_limit_error(
        self, mock_logger, mock_client_ai
    ):
        """속도 제한 오류 처리 검증"""
        from solar_system_sim_v2_openai import RateLimitError

        mock_client_ai.client.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit", response=MagicMock(), body={}
        )

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # 속도 제한 오류는 None 반환
        assert result is None
        mock_logger.warning.assert_called()

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_api_connection_error(
        self, mock_logger, mock_client_ai
    ):
        """API 연결 오류 처리 검증"""
        from solar_system_sim_v2_openai import APIConnectionError

        mock_client_ai.client.chat.completions.create.side_effect = (
            APIConnectionError(message="Connection failed", request=MagicMock())
        )

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # 연결 오류는 None 반환
        assert result is None
        mock_logger.error.assert_called()

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_generic_api_error(
        self, mock_logger, mock_client_ai
    ):
        """일반적인 API 오류 처리 검증"""
        from solar_system_sim_v2_openai import APIError

        mock_client_ai.client.chat.completions.create.side_effect = APIError(
            message="Unknown error", request=MagicMock(), body={}
        )

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # API 오류는 None 반환
        assert result is None
        mock_logger.error.assert_called()

    @patch('solar_system_sim_v2_openai.logger')
    def test_interpret_scenario_handles_unexpected_exception(
        self, mock_logger, mock_client_ai
    ):
        """예상치 못한 오류 처리 검증"""
        mock_client_ai.client.chat.completions.create.side_effect = ValueError(
            "Unexpected error"
        )

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        result = mock_client_ai.interpret_scenario(scenario)

        # 예상치 못한 오류는 None 반환, exception 로깅
        assert result is None
        mock_logger.exception.assert_called()


class TestAIInterpreterBuildPrompt:
    """AIInterpreter._build_prompt() 검증"""

    @pytest.fixture
    def ai(self):
        """테스트용 AIInterpreter"""
        ai = AIInterpreter()
        ai.client = MagicMock()  # Mock 클라이언트 설정
        return ai

    def test_build_prompt_sun_mass_scenario(self, ai):
        """태양 질량 변화 시나리오 프롬프트 생성 검증"""
        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }
        prompt = ai._build_prompt(scenario)

        # 프롬프트에 필요한 정보 포함 확인
        assert '1.0%' in prompt or '1.0' in prompt
        assert '0.5' in prompt
        assert '지구' in prompt or '공전' in prompt

    def test_build_prompt_earth_mass_scenario(self, ai):
        """지구 질량 변화 시나리오 프롬프트 생성 검증"""
        scenario = {
            'type': ScenarioType.EARTH_MASS.value,
            'percent_change': 2.0,
            'results': {'surface_gravity_change_pct': 2.0},
        }
        prompt = ai._build_prompt(scenario)

        assert '2.0%' in prompt or '2.0' in prompt
        assert '표면' in prompt or '중력' in prompt

    def test_build_prompt_blackhole_scenario(self, ai):
        """블랙홀 시나리오 프롬프트 생성 검증"""
        scenario = {'type': ScenarioType.BLACKHOLE.value}
        prompt = ai._build_prompt(scenario)

        assert '블랙홀' in prompt
        assert 'AU' in prompt

    def test_build_prompt_sirius_scenario(self, ai):
        """시리우스 시나리오 프롬프트 생성 검증"""
        scenario = {'type': ScenarioType.SIRIUS.value}
        prompt = ai._build_prompt(scenario)

        assert '시리우스' in prompt or '별' in prompt

    def test_build_prompt_unknown_scenario_raises_error(self, ai):
        """알 수 없는 시나리오 타입 오류 발생 검증"""
        scenario = {'type': 'unknown_scenario_type'}

        with pytest.raises(ValueError, match='알 수 없는 시나리오 타입'):
            ai._build_prompt(scenario)

    def test_build_prompt_uses_get_for_safe_access(self, ai):
        """프롬프트 생성이 .get()으로 안전하게 접근 검증 (KeyError 방지)"""
        # 필수 키가 없는 시나리오도 처리 가능해야 함
        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            # 'percent_change'와 'results' 누락
        }

        # KeyError가 발생하지 않고 기본값을 사용해야 함
        prompt = ai._build_prompt(scenario)
        assert isinstance(prompt, str)
        assert len(prompt) > 0


# ============================================================================
# 4. 통합 테스트
# ============================================================================


class TestIntegration:
    """통합 테스트"""

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('solar_system_sim_v2_openai.OpenAI')
    def test_full_scenario_workflow(self, mock_openai_class):
        """전체 워크플로우 검증"""
        # Mock 클라이언트 설정
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock 응답 설정
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="시뮬레이션 해석 결과"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # 엔진 및 AI 초기화
        planets = {
            'Earth': Planet('지구', 1.0, 1.0, 1.0, 288),
            'Mars': Planet('화성', 0.107, 0.532, 1.524, 210),
        }
        engine = SimulationEngine(planets)
        ai = AIInterpreter()

        # 시나리오 생성 및 해석
        scenario = engine.scenario_sun_mass_change(1.0)
        result = ai.interpret_scenario(scenario)

        # 결과 검증
        assert result == "시뮬레이션 해석 결과"
        assert scenario['type'] == ScenarioType.SUN_MASS.value


# ============================================================================
# 5. 보안 테스트
# ============================================================================


class TestSecurity:
    """보안 관련 테스트"""

    @pytest.fixture
    def ai(self):
        """테스트용 AIInterpreter"""
        ai = AIInterpreter()
        ai.client = MagicMock()
        return ai

    def test_api_key_not_logged(self, ai, caplog):
        """API Key가 로그에 노출되지 않는지 검증"""
        ai.api_key = 'sk-proj-test-key-12345'

        scenario = {
            'type': ScenarioType.SUN_MASS.value,
            'percent_change': 1.0,
            'results': {'Earth': {'orbital_period_change_pct': 0.5}},
        }

        # 로그 캡처 후 해석 실행
        with caplog.at_level(logging.ERROR):
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content="응답"))
            ]
            ai.client.chat.completions.create.return_value = mock_response
            ai.interpret_scenario(scenario)

        # 로그에 API Key가 없는지 확인
        assert 'sk-proj' not in caplog.text
        assert 'test-key' not in caplog.text

    def test_error_messages_no_internal_details(self, ai):
        """에러 메시지가 내부 세부사항을 노출하지 않는지 검증"""
        scenario = {'type': 'invalid_type'}

        # 알 수 없는 타입으로 인한 오류는 로깅되고 None 반환
        result = ai.interpret_scenario(scenario)
        assert result is None


# ============================================================================
# 6. 회귀 테스트
# ============================================================================


@pytest.mark.parametrize(
    "scenario_type,expected_in_prompt",
    [
        (ScenarioType.SUN_MASS.value, ['지구', '공전']),
        (ScenarioType.EARTH_MASS.value, ['표면', '중력']),
        (ScenarioType.BLACKHOLE.value, ['블랙홀', 'AU']),
        (ScenarioType.SIRIUS.value, ['시리우스']),
    ],
)
def test_build_prompt_all_scenario_types(scenario_type, expected_in_prompt):
    """모든 시나리오 타입에 대한 회귀 테스트"""
    ai = AIInterpreter()
    ai.client = MagicMock()

    scenario = {'type': scenario_type}
    prompt = ai._build_prompt(scenario)

    for keyword in expected_in_prompt:
        assert keyword in prompt, f"'{keyword}'가 프롬프트에 없음: {prompt}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
