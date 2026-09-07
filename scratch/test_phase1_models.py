"""
Phase 1 Schema Verification Script
Tests inserting and reading back a full mock interview session across all 8 tables,
and verifies database-level foreign key enforcement.
"""

from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import (
    CandidateProfile,
    Claim,
    Evaluation,
    Evidence,
    EvidenceType,
    RoleProfile,
    Session,
    SessionStatus,
    Speaker,
    StateTransition,
    Turn,
)


def run_phase_1_verification():
    db = SessionLocal()
    print("=== Starting Phase 1 Schema Verification ===")

    try:
        # 1. Create CandidateProfile
        candidate = CandidateProfile(
            raw_resume_text="Harsh Gupta\nSoftware Engineer\nSkills: Python, FastAPI, PostgreSQL",
            extracted_json={
                "candidate_name": "Harsh Gupta",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "projects": [
                    {
                        "name": "Miki Interview Engine",
                        "description": "Voice-first AI interview system",
                    }
                ],
                "claims": [
                    {
                        "claim_text": "Built async ingestion pipeline handling 10k req/s",
                        "category": "performance",
                    }
                ],
            },
        )
        db.add(candidate)
        db.flush()
        print(f"[OK] Created CandidateProfile (id={candidate.id})")

        # 2. Create RoleProfile
        role = RoleProfile(
            raw_jd_text="Senior Backend Engineer\nRequirements: Python, Distributed Systems, SQL",
            extracted_json={
                "role_title": "Senior Backend Engineer",
                "required_skills": ["Python", "Distributed Systems", "SQL"],
                "seniority_signal": "Senior",
            },
        )
        db.add(role)
        db.flush()
        print(f"[OK] Created RoleProfile (id={role.id})")

        # 3. Create Session
        session = Session(
            candidate_profile_id=candidate.id,
            role_profile_id=role.id,
            mode="normal",
            status=SessionStatus.IN_PROGRESS,
            policy_version="1.0.0",
            engine_version="1.0.0",
        )
        db.add(session)
        db.flush()
        print(f"[OK] Created Session (id={session.id}, status={session.status})")

        # 4. Create Turns (Miki question + Candidate answer)
        turn_1 = Turn(
            session_id=session.id,
            turn_index=1,
            speaker=Speaker.MIKI,
            text="Could you walk me through how you designed your ingestion pipeline?",
        )
        db.add(turn_1)
        db.flush()

        turn_2 = Turn(
            session_id=session.id,
            turn_index=2,
            speaker=Speaker.CANDIDATE,
            text="We used Python async workers with a partitioned message queue to handle 10k req/s.",
        )
        db.add(turn_2)
        db.flush()
        print(f"[OK] Created Turns (turn 1 id={turn_1.id}, turn 2 id={turn_2.id})")

        # 5. Create Claim extracted from Candidate Turn
        claim = Claim(
            session_id=session.id,
            turn_id=turn_2.id,
            claim_text="Handled 10k req/s using Python async workers and partitioned queues",
            category="performance",
            confidence=0.92,
        )
        db.add(claim)
        db.flush()
        print(f"[OK] Created Claim (id={claim.id}, confidence={claim.confidence})")

        # 6. Create Evidence for the Claim
        evidence = Evidence(
            claim_id=claim.id,
            turn_id=turn_2.id,
            evidence_text="Candidate explicitly cited queue partitioning and async workers",
            evidence_type=EvidenceType.SUPPORTS,
        )
        db.add(evidence)
        db.flush()
        print(
            f"[OK] Created Evidence (id={evidence.id}, type={evidence.evidence_type})"
        )

        # 7. Create StateTransition record
        transition = StateTransition(
            session_id=session.id,
            from_state="OPENING",
            to_state="PROBING_CLAIM",
            proposed_by_llm=True,
            was_validated=True,
            rejection_reason=None,
            model_id="deepseek/deepseek-v3",
        )
        db.add(transition)
        db.flush()
        print(
            f"[OK] Created StateTransition (from={transition.from_state} to={transition.to_state})"
        )

        # 8. Create Evaluation record
        eval_record = Evaluation(
            session_id=session.id,
            dimension="system_design",
            score=8.5,
            evidence_refs=[evidence.id],
            rubric_version="1.0.0",
            model_id="anthropic/claude-sonnet-4.5",
        )
        db.add(eval_record)
        db.flush()
        print(
            f"[OK] Created Evaluation (dimension={eval_record.dimension}, score={eval_record.score})"
        )

        # Commit transaction
        db.commit()
        print("\n--- Testing Relationship Traversal ---")

        # Query back through relationships
        retrieved_session = db.query(Session).filter(Session.id == session.id).one()
        assert len(retrieved_session.turns) == 2, "Turns relationship failed"
        assert len(retrieved_session.claims) == 1, "Claims relationship failed"
        assert len(retrieved_session.state_transitions) == 1, (
            "Transitions relationship failed"
        )
        assert len(retrieved_session.evaluations) == 1, (
            "Evaluations relationship failed"
        )
        assert (
            retrieved_session.candidate_profile.extracted_json["candidate_name"]
            == "Harsh Gupta"
        )
        assert (
            retrieved_session.claims[0].evidence_items[0].evidence_type
            == EvidenceType.SUPPORTS
        )

        print(
            f"[OK] Relationship queries passed! Session has {len(retrieved_session.turns)} turns, {len(retrieved_session.claims)} claims."
        )

        # 9. Test Foreign Key Constraint Enforcement
        print("\n--- Testing Foreign Key Integrity Constraint ---")
        orphaned_turn = Turn(
            session_id=99999999,  # Non-existent session
            turn_index=99,
            speaker=Speaker.CANDIDATE,
            text="This turn should fail to insert due to FK violation.",
        )
        db.add(orphaned_turn)
        try:
            db.commit()
            raise AssertionError(
                "Foreign key constraint failed: Orphaned turn was inserted!"
            )
        except IntegrityError:
            db.rollback()
            print(
                "[OK] Database successfully rejected orphaned turn with IntegrityError (Foreign Key enforced)!"
            )

        print("\n=== Checkpoint 1 PASSED: All 8 models verified successfully! ===")

    except Exception as e:
        db.rollback()
        print(f"[FAIL] Verification failed with error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_phase_1_verification()
