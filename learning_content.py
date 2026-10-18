"""Plain-language explanations built from calculated orbital results."""


def explain_for_learners(settings, elements, baseline):
    """Explain the selected model without turning escape trajectories into years."""
    mass_percent = round(settings["mass"] * 100)
    radius_percent = round(settings["radius"] * 100)
    state = elements["state"]
    shape = "circle" if state == "circle" else "ellipse" if elements["bound"] else "escape"
    shapes = {"circle": "동그란 길", "ellipse": "길쭉한 타원 모양의 길", "escape": "다시 돌아오지 않는 열린 길"}
    period = elements["period_days"]
    days = round(period) if period is not None else None
    if not elements["bound"]:
        headline = "지구가 태양을 떠나는 길로 움직여요."
        reason = "태양이 갑자기 가벼워져서, 지금 속도로 움직이는 지구를 붙잡기 어려워졌어요. 지구는 태양을 한 바퀴 도는 대신 멀어져요."
        period_text = "한 바퀴 돌지 않아요"
        comparison = "되돌아오는 공전 주기를 정할 수 없어요."
    else:
        headline = "지구가 동그란 길을 따라 돌아요." if shape == "circle" else "지구가 길쭉한 타원 모양으로 돌아요."
        if settings["model"] == "circular":
            reason = "이번에는 태양의 질량에 맞는 속도로 지구를 출발시켰어요. 그래서 도는 길이 동그랗게 유지돼요."
        elif shape == "circle":
            reason = "태양의 질량을 현재와 같게 두었어요. 처음에 동그랗게 돌던 지구는 같은 길을 계속 돌아요."
        else:
            reason = "태양의 질량이 바뀌어도 그 순간 지구의 속도는 그대로예요. 태양이 끌어당기는 힘과 지구의 움직임이 달라져 도는 길이 바뀌어요."
        period_text = f"약 {days:,}일"
        difference = period - baseline["period_days"]
        if abs(difference) < 0.5:
            comparison = "같은 거리에서 현재 태양을 돌 때와 같아요."
        else:
            comparison = f"현재 태양일 때의 약 {round(baseline['period_days']):,}일보다 {'더 오래 걸려요' if difference > 0 else '더 빨리 돌아요'}."
    return {
        "shape": shape, "shape_text": shapes[shape], "headline": headline, "reason": reason,
        "period_days_rounded": days, "period_text": period_text, "period_comparison": comparison,
        "mass_percent": mass_percent, "radius_percent": radius_percent,
        "conditions": f"태양의 질량: 현재의 {mass_percent}% · 처음 거리: 현재 지구 거리의 {radius_percent}%",
        "model_note": "질량이 바뀌는 순간 지구의 위치와 속도는 그대로예요." if settings["model"] == "impulse" else "처음부터 이 질량의 태양 주위를 동그랗게 돌도록 출발해요.",
        "observation_starter": f"태양의 질량을 현재의 {mass_percent}%로 두고 처음 거리를 {radius_percent}%로 설정했다. 지구는 {shapes[shape]}을 따라 움직였다. " + (f"한 바퀴 도는 데 약 {days:,}일이 걸렸다." if days is not None else "태양을 한 바퀴 돌지 않아 공전 주기를 정할 수 없었다."),
    }
