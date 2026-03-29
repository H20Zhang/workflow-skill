VALID_SPEC = """goal: Deliver a validated answer to the user
initial_state: intake
terminal_states: done

state: intake
  instructions:
    - Understand the request and record the user's constraints.
  state_skills: require_goal_alignment, collect_evidence
  transitions:
    - to: plan
      when: enough notes exist to define a plan
      guidance: Turn the captured notes into a concrete plan for the planning phase.
      skills: require_notes

state: plan
  instructions:
    - Produce a stepwise plan tied to the final goal.
  state_skills: require_goal_alignment
  transitions:
    - to: execute
      when: the plan is ready
      guidance: Promote the approved plan into concrete execution work.
      skills: require_plan_ready
    - to: intake
      when: constraints are still missing
      guidance: Return to intake and gather the missing constraints before planning again.

state: execute
  instructions:
    - Perform the work and store the result artifact.
  transitions:
    - to: done
      when: the result and final goal are both complete
      guidance: Package the result, confirm the final goal, and close the workflow.
      skills: require_artifact, require_goal_complete

state: done
  instructions:
    - Present the final result and stop.
"""

MALFORMED_SPEC = """goal: Broken example
initial_state: intake
terminal_states: done

state: intake
  instructions:
    collect requirements without a bullet
"""

MISSING_GOAL_SPEC = """initial_state: intake
terminal_states: done

state: intake
  instructions:
    - Gather requirements.
  transitions:
    - to: done
      guidance: Move to completion once requirements are gathered.

state: done
  instructions:
    - Stop.
"""

MISSING_GUIDANCE_SPEC = """goal: Missing guidance example
initial_state: intake
terminal_states: done

state: intake
  instructions:
    - Gather requirements.
  transitions:
    - to: done
      when: the work is done

state: done
  instructions:
    - Stop.
"""

UNKNOWN_TARGET_SPEC = """goal: Unknown target example
initial_state: intake
terminal_states: done

state: intake
  instructions:
    - Gather requirements.
  transitions:
    - to: missing
      guidance: Attempt to go to a state that does not exist.

state: done
  instructions:
    - Stop.
"""

UNREACHABLE_STATE_SPEC = """goal: Reachability example
initial_state: intake
terminal_states: done

state: intake
  instructions:
    - Gather requirements.
  transitions:
    - to: done
      guidance: Move to completion.

state: done
  instructions:
    - Stop.

state: orphan
  instructions:
    - This state cannot be reached.
  transitions:
    - to: done
      guidance: Move to completion.
"""

AMBIGUOUS_TRANSITION_SPEC = """goal: Ambiguous selector example
initial_state: review
terminal_states: done

state: review
  instructions:
    - Inspect the request.
  transitions:
    - to: execute
      when: the fast path is acceptable
      guidance: Go directly into execution via the fast path.
    - to: execute
      when: the thorough path is required
      guidance: Go directly into execution via the thorough path.

state: execute
  instructions:
    - Perform the work.
  transitions:
    - to: done
      guidance: Finish the workflow.

state: done
  instructions:
    - Stop.
"""
