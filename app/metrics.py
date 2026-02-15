
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

    avg_session = round((total_minutes/total_sessions if total_sessions > 0 else 0), 2)

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
    outcome_rate = outcome_exists / total_sessions if total_sessions > 0 else 0
    # Calculate variables needed for observation logic
    long_fail_diff = long_sessions_without_outcome - long_sessions_with_outcome
    short_fail_diff = short_sessions_without_outcome - short_sessions_with_outcome
    short_success_diff = short_sessions_with_outcome - short_sessions_without_outcome

    # Calculate outcome completion rates (reliability)
    short_outcome_rate = (
        short_sessions_with_outcome / (short_sessions_with_outcome + short_sessions_without_outcome)
        if (short_sessions_with_outcome + short_sessions_without_outcome) > 0 else 0
    )
    long_outcome_rate = (
        long_sessions_with_outcome / (long_sessions_with_outcome + long_sessions_without_outcome)
        if (long_sessions_with_outcome + long_sessions_without_outcome) > 0 else 0
    )

    # New metrics: Average outcome quality (not per minute)
    avg_outcome_length_short = (
        total_outcome_short / short_sessions_with_outcome
        if short_sessions_with_outcome > 0 else 0
    )

    avg_outcome_length_long = (
        total_outcome_long / long_sessions_with_outcome
        if long_sessions_with_outcome > 0 else 0
    )
    # Combined effectiveness: quality × reliability
    short_effectiveness = avg_outcome_length_short * short_outcome_rate
    long_effectiveness = avg_outcome_length_long * long_outcome_rate

    # Calculate differences
    quality_diff = avg_outcome_length_short - avg_outcome_length_long
    reliability_diff = short_outcome_rate - long_outcome_rate
    effectiveness_diff = short_effectiveness - long_effectiveness

    # Adaptive buffer
    min_buffer = 0.03
    max_buffer = 0.20
    min_sessions_for_full = 12
    effective_buffer = max_buffer - (max_buffer - min_buffer) * min(1.0, total_sessions / min_sessions_for_full)
    # Thresholds
    quality_buffer = 15  # characters difference
    effectiveness_buffer = effective_buffer * 100  # scaled for effectiveness
    # --- EFFECTIVENESS MESSAGE ---
    if total_sessions < 3:
        summary_message = "Not enough data yet to identify patterns in session effectiveness."
    elif (quality_diff < -quality_buffer and long_outcome_rate >= short_outcome_rate):
        summary_message = "Longer sessions produce more detailed outcomes and maintain high completion rates."
    elif (quality_diff > quality_buffer and short_outcome_rate >= long_outcome_rate):
        summary_message = "Shorter sessions produce more detailed outcomes and maintain high completion rates."
    elif abs(quality_diff) < quality_buffer and reliability_diff > 0.2:
        summary_message = "Shorter sessions are more reliable—you complete them more consistently."
    elif abs(quality_diff) < quality_buffer and reliability_diff < -0.2:
        summary_message = "Longer sessions are more reliable—you complete them more consistently."
    elif quality_diff < -quality_buffer and short_outcome_rate > long_outcome_rate:
        summary_message = "Longer sessions produce richer outcomes, but shorter sessions complete more reliably."
    elif quality_diff > quality_buffer and long_outcome_rate > short_outcome_rate:
        summary_message = "Shorter sessions produce richer outcomes, but longer sessions complete more reliably."
    else:
        summary_message = "Session length does not significantly affect outcome quality in this project."
    # --- RELIABILITY MESSAGE ---
    if total_sessions < 3:
        reliability_message = "Track a few more sessions to establish reliability patterns."
    elif outcome_rate >= 0.8:
        reliability_message = "Excellent consistency—nearly all sessions produce recorded outcomes."
    elif outcome_rate >= 0.7:
        reliability_message = "Good consistency—most sessions end with clear outcomes."
    elif outcome_rate >= 0.5:
        reliability_message = "Moderate consistency—about half of sessions end with documented outcomes."
    elif outcome_rate >= 0.3:
        reliability_message = "Low consistency—many sessions end without recorded outcomes, making progress harder to track."
    else:
        reliability_message = "Very low consistency—most sessions lack outcome records, which limits learning and momentum."

    # --- OBSERVATION MESSAGE ---
    observation_message = None
    if total_sessions < 3:
        observation_message = None
    elif long_fail_diff >= 2 and long_sessions_without_outcome > long_sessions_with_outcome:
        observation_message = "Long sessions frequently end without concrete outcomes—consider breaking them into smaller chunks."
    elif short_fail_diff >= 2 and short_sessions_without_outcome > short_sessions_with_outcome:
        observation_message = "Short sessions often lack closure—you may need more time to reach clear stopping points."
    elif short_success_diff >= 2 and short_outcome_rate > 0.7:
        observation_message = "Short sessions consistently produce clear outcomes—this rhythm works well for you."
    elif long_outcome_rate > 0.8 and long_sessions_with_outcome >= 2:
        observation_message = "Extended focus sessions are highly productive when you commit to them fully."
    elif outcome_rate < 0.4:
        observation_message = "Sessions often end abruptly without summary—this makes it harder to build momentum between work periods."

    # --- RECOMMENDATION ---
    recommendation = ""

    if total_sessions < 3:
        recommendation = "Continue tracking sessions. After 5-10 sessions, clearer patterns will emerge to guide your workflow."
    elif effectiveness_diff < -effectiveness_buffer and long_outcome_rate >= 0.7:
        recommendation = "Your data strongly favors longer, focused sessions. Schedule 90-120 minute blocks of uninterrupted deep work when possible."
    elif effectiveness_diff > effectiveness_buffer and short_outcome_rate >= 0.7:
        recommendation = "Your data strongly favors shorter, focused sessions. Aim for 30-60 minute blocks with clear outcomes rather than marathon sessions."
    elif outcome_rate < 0.3:
        recommendation = "Start simple: at the end of EVERY session, write one sentence about what you accomplished. This single habit will transform your productivity tracking."
    elif outcome_rate < 0.5:
        if short_outcome_rate > long_outcome_rate + 0.2:
            recommendation = "You close short sessions more reliably. Try working in focused 30-45 minute blocks with mandatory outcome notes."
        else:
            recommendation = "Build the habit of ending every session with a brief outcome summary—even if it's just 'explored X, blocked by Y'."
    elif long_fail_diff >= 2:
        recommendation = "Long sessions often lose focus. Try the Pomodoro technique: work 25-50 minutes, document outcomes, then decide whether to continue or stop."
    elif short_fail_diff >= 2:
        recommendation = "Short sessions may be too brief to reach meaningful stopping points. Try extending to 45-60 minutes with a clear mini-goal."
    elif outcome_rate >= 0.8 and abs(quality_diff) < quality_buffer / 2:
        recommendation = "Your session discipline is excellent. Focus on the work itself—your tracking habits are solid."
    else:
        if long_effectiveness > short_effectiveness * 1.1:
            recommendation = "Longer sessions tend to work better for you. Consider protecting 90+ minute blocks for deep, focused work."
        elif short_effectiveness > long_effectiveness * 1.1:
            recommendation = "Shorter sessions appear more productive. Try working in focused 45-60 minute sprints."
        elif avg_outcome_length_long > avg_outcome_length_short + 5:
            recommendation = "Longer sessions produce slightly more detailed outcomes. Give yourself time for deep work when possible."
        elif avg_outcome_length_short > avg_outcome_length_long + 5:
            recommendation = "Shorter sessions produce slightly more detailed outcomes. Focused sprints seem to work well for you."
        else:
            recommendation = "Session length appears flexible for your workflow. Prioritize clear outcome documentation regardless of duration."

    # Then continue with the rest of the logic...

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
