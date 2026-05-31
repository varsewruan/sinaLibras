"""Progress and gamification."""


async def _first_lesson(client):
    phases = (await client.get("/api/learning/phases")).json()
    lesson = phases[0]["lessons"][0]
    return lesson  # has id + xp_reward


async def test_complete_lesson_awards_xp_proportional_to_score(auth_client):
    lesson = await _first_lesson(auth_client)
    r = await auth_client.post(
        "/api/progress/complete-lesson",
        json={"lesson_id": lesson["id"], "score": 80},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is True
    assert body["awarded_xp"] == round(lesson["xp_reward"] * 80 / 100)
    assert body["user"]["xp"] == body["awarded_xp"]
    assert body["streak"]["current"] == 1


async def test_failing_attempt_awards_no_xp(auth_client):
    lesson = await _first_lesson(auth_client)
    r = await auth_client.post(
        "/api/progress/complete-lesson",
        json={"lesson_id": lesson["id"], "score": 40},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["passed"] is False
    assert body["awarded_xp"] == 0
    assert body["user"]["xp"] == 0


async def test_second_pass_does_not_double_award_xp(auth_client):
    lesson = await _first_lesson(auth_client)
    first = await auth_client.post("/api/progress/complete-lesson",
                                   json={"lesson_id": lesson["id"], "score": 80})
    xp_after_first = first.json()["user"]["xp"]

    second = await auth_client.post("/api/progress/complete-lesson",
                                    json={"lesson_id": lesson["id"], "score": 100})
    body = second.json()
    assert body["awarded_xp"] == 0, "already-passed lessons don't farm XP on replay"
    assert body["user"]["xp"] == xp_after_first


async def test_score_keeps_best_after_replay(auth_client):
    lesson = await _first_lesson(auth_client)
    await auth_client.post("/api/progress/complete-lesson",
                           json={"lesson_id": lesson["id"], "score": 70})
    await auth_client.post("/api/progress/complete-lesson",
                           json={"lesson_id": lesson["id"], "score": 50})
    phases = (await auth_client.get("/api/learning/phases")).json()
    completed = phases[0]["lessons"][0]
    assert completed["score"] == 70, "best score wins, lower replays don't overwrite"
    assert completed["completed"] is True


async def test_progress_for_unknown_lesson_returns_404(auth_client):
    r = await auth_client.post(
        "/api/progress/complete-lesson",
        json={"lesson_id": "ghost", "score": 100},
    )
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "lesson_not_found"


async def test_summary_reflects_completions(auth_client):
    lesson = await _first_lesson(auth_client)
    await auth_client.post("/api/progress/complete-lesson",
                           json={"lesson_id": lesson["id"], "score": 80})
    r = await auth_client.get("/api/progress/me/summary")
    body = r.json()
    assert body == {"lessons_started": 1, "lessons_completed": 1, "best_average": 80}


async def test_complete_lesson_requires_auth(client):
    lesson = await _first_lesson(client)
    r = await client.post(
        "/api/progress/complete-lesson",
        json={"lesson_id": lesson["id"], "score": 80},
    )
    assert r.status_code == 401
