
from sqlalchemy import func, or_

def insights_analyzer(project_id, db, WorkSession):
    sessions = WorkSession.query.filter_by(project_id = project_id).all()
    total_sessions = db.session.query(
        func.count(WorkSession.id)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    total_minutes = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    avg_session = (total_minutes/total_sessions if total_sessions > 0 else 0)

    max_session = db.session.query(
        func.max(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0

    min_session = db.session.query(
        func.min(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id
    ).scalar() or 0


    outcome_doesnt_exists = db.session.query(
        func.count(WorkSession.id)
    ).filter(
        WorkSession.project_id == project_id, WorkSession.outcome == ''
    ).scalar() or 0

    outcome_exists = total_sessions - outcome_doesnt_exists

    time_without_outcome = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id, 
        WorkSession.outcome == ''
    ).scalar() or 0

    time_with_outcome = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id, 
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0


    long_sessions_with_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes > avg_session,
            WorkSession.outcome.isnot(None),
            WorkSession.outcome != ''
        )
        .scalar()
    ) or 0

    long_sessions_without_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes > avg_session,
            or_(
                WorkSession.outcome.is_(None),
                WorkSession.outcome == ''
            )
        )
        .scalar()
    ) or 0

    short_sessions_with_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes < avg_session,
            WorkSession.outcome.isnot(None),
            WorkSession.outcome != ''
        )
        .scalar()
    ) or 0

    short_sessions_without_outcome = (
        db.session.query(func.count(WorkSession.id))
        .filter(
            WorkSession.project_id == project_id,
            WorkSession.duration_minutes < avg_session,
            or_(
                WorkSession.outcome.is_(None),
                WorkSession.outcome == ''
            )
        )
        .scalar()
    ) or 0

    total_outcome_long = db.session.query(
        func.sum(func.length(WorkSession.outcome))
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes > avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    total_duration_long = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes > avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    outcome_density_long = (
        total_outcome_long / total_duration_long
        if total_duration_long > 0 else 0
    )


    total_outcome_short = db.session.query(
        func.sum(func.length(WorkSession.outcome))
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes < avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    total_duration_short = db.session.query(
        func.sum(WorkSession.duration_minutes)
    ).filter(
        WorkSession.project_id == project_id,
        WorkSession.duration_minutes < avg_session,
        WorkSession.outcome.isnot(None),
        WorkSession.outcome != ''
    ).scalar() or 0

    outcome_density_short = (
        total_outcome_short / total_duration_short
        if total_duration_short > 0 else 0
    )
    
    # Adaptive buffer: higher (more conservative) on small data, drops to min_buffer as sessions grow
    min_buffer = 0.08                  # target for large projects
    max_buffer = 0.25                  # conservative for very small projects
    min_sessions_for_full = 12         # after this many sessions, use full sensitivity

    effective_buffer = max_buffer - (max_buffer - min_buffer) * min(1.0, total_sessions / min_sessions_for_full)

    # 1. Effectiveness / Density comparison (now using adaptive buffer)
    density_diff = outcome_density_short - outcome_density_long

    if density_diff > effective_buffer:
        summary_message = "Shorter sessions tend to produce clearer outcomes per minute than longer sessions."
    elif density_diff < -effective_buffer:
        summary_message = "Longer sessions appear to generate more outcome value per minute than shorter ones."
    else:
        summary_message = "Session length does not significantly affect outcome quality in this project."

    # 2. Reliability / Outcome rate (unchanged — good as is)
    outcome_rate = outcome_exists / total_sessions if total_sessions > 0 else 0
    if outcome_rate >= 0.7:
        reliability_message = "Most sessions produce a recorded outcome. Your work is consistent."
    elif 0.4 <= outcome_rate < 0.7:
        reliability_message = "Outcomes are produced inconsistently. Some sessions may lack clear closure."
    else:
        reliability_message = "Many sessions end without a recorded outcome. This may reduce learning clarity."

    # 3. Observation — keep only ONE (strongest failure first)
    observation_message = None

    long_fail_diff = long_sessions_without_outcome - long_sessions_with_outcome
    short_success_diff = short_sessions_with_outcome - short_sessions_without_outcome

    if long_fail_diff > 1.5 or long_fail_diff > short_success_diff:
        observation_message = "Long sessions often end without a concrete outcome."
    elif short_success_diff > 1.5:
        observation_message = "Short sessions frequently result in clear outcomes."

    # 4. Recommendation — one final message, with soft override for low rate
    recommendation = ""

    if outcome_rate < 0.4:
        recommendation = "Many sessions end without a clear outcome. Make it a habit to explicitly record what was achieved at the end of each session."
        # Optional soft add-on if short is clearly better even when rate is low
        if density_diff > 0.3:
            recommendation += " Shorter sessions already show clearer results when you do close them."
    else:
        # Normal density-based recommendation (using the same adaptive buffer)
        if density_diff > effective_buffer:
            recommendation = "Try working in shorter, focused sessions and explicitly closing each session with a written outcome."
        elif density_diff < -effective_buffer:
            recommendation = "Longer uninterrupted sessions seem to work better for this project. Protect time for deep work."
        else:
            recommendation = "Session length appears flexible. Focus on clearly defining outcomes regardless of session duration."

    insights = {
        "effectiveness": summary_message,
        "reliability": reliability_message,
        "observation": observation_message,
        "recommendation" : recommendation
    }

    return (sessions, project_id,
        total_minutes,
        total_sessions,
        avg_session,
        insights,
        outcome_exists
    )
