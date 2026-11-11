"""The design track's wording agrees across planning, readiness, the forms, the skills, and the designer agent."""
from conftest import AGENTS, ASSETS, REFERENCES, SKILLS, read


def prose(path):
    return " ".join(read(path).split())


def skill(name):
    return prose(SKILLS / name / "SKILL.md")


def reference(name):
    return prose(REFERENCES / f"{name}.md")


def designer():
    return prose(AGENTS / "orchi-designer.agent.md")


def form(name):
    return read(ASSETS / "issues" / name)


def test_planning_sets_design_depth_and_only_the_user_chooses_a_direction():
    planning, plan = reference("planning"), skill("orchi-plan")
    for depth in ("| None |", "| Brief |", "| Epic |"):
        assert depth in planning
    assert "Plan a standalone `design` Epic (labels `Epic` and `design`) for a designer crew, outside any Initiative" in planning
    assert "`Deferred until #<design Epic>`" in planning and "blocked by the design Epic" in planning
    assert "Only the user names references, chooses the engine and a direction, and approves a comp or a generated asset, or Orchi in autonomous mode." in planning
    assert "a new product picks it in its exploration's design session, and a project without either picks it in its first design Epic" in planning
    assert "planning.md#user-interface-design" in plan
    assert "agree the references and the surface brief with the user now" in plan
    assert "a design Epic leaves references, the engine, and the direction to its designer" in plan


def test_ui_readiness_items_have_form_fields():
    assert reference("readiness").count("planning.md#user-interface-design") == 2
    for name in ("task.yml", "epic.yml"):
        text = form(name)
        assert "id: ui" in text and "label: UI design" in text


def test_designer_crew_role_routing_and_mode_agree():
    pool, design = reference("pool"), skill("orchi-design")
    assert "| Designer | `orchi-design` | One standalone `design` Epic, with the user |" in pool
    assert '"Take #n" on a `delivery-ready` Epic labelled `design` | Designer | `orchi-design`' in pool
    assert "Only the user names references, chooses the engine and a direction, and approves a comp or a generated asset, or Orchi in autonomous mode" in design
    assert "Continue with [orchi-deliver](../orchi-deliver/SKILL.md)" in design
    assert "Ask the user directly while autonomous mode is off, and Orchi while it is on" in design and "Adopt Orchi's claim" in design
    assert "asks for orchi-design by name" in design
    assert "`ask_user`" in design and "`agent_type: orchi-designer`" in design
    assert "(../orchi-core/references/roles.md#design-skills)" in design and "does not bundle them" in design
    assert "(../orchi-core/references/canvases.md#the-design-board)" in design


def test_exploration_records_product_truth_and_references():
    exploration, design = reference("exploration"), skill("orchi-design")
    assert "| Product | For a product with a user interface" in exploration
    assert "The first design Epic writes `PRODUCT.md` from it and asks only what is missing" in exploration
    assert "How screens should look is not settled here" not in exploration
    assert "id: product" in form("exploration.yml")
    assert "write it with the user from the Product section of the Exploration" in design


def test_delivery_routes_ui_tasks_to_the_designer_and_audits_ui_changes():
    roles, review, deliver = reference("roles"), reference("review-delivery"), skill("orchi-deliver")
    assert "every Task that builds against a surface brief or an approved comp" in roles
    assert "a direction, a comp, or a generated asset goes to the user whatever they delegated" in roles
    assert "start `orchi-designer` in Audit mode on it beside the reviewer" in review
    assert "`orchi-designer` in Audit mode" in deliver


def test_design_outputs_that_bind_later_work_pass_the_user():
    agent, roles, design, planning = designer(), reference("roles"), skill("orchi-design"), reference("planning")
    assert "Never write or replace `DESIGN.md`" in agent
    assert "Commit a generated asset only when the Issue links that asset as approved" in agent
    assert "the `DESIGN.md` sections it follows when `DESIGN.md` exists" in agent
    assert "**Recheck (Audit mode):**" in agent
    assert "write or replace `DESIGN.md` from the built surfaces with the user and commit it" in design
    assert "`Design engine: <Hallmark | prototype>`" in design
    assert "| `PRODUCT.md`, references, surface briefs, the engine and direction rounds, comp and asset approval, `DESIGN.md` | The session that talks to the user" in roles
    assert "Commit the brief on the work's branch, which planning creates now" in planning
    assert "impeccable" not in planning.lower()
    assert "the branch of work at design depth brief" in skill("orchi-plan")
    assert "for a `decision` `ESCALATE`" in skill("orchi-work")
    assert "surface briefs and approved comps in `docs/design/surfaces/`" in reference("knowledge")


def test_first_design_epic_runs_both_engines_and_the_user_picks_one():
    design, agent = skill("orchi-design"), designer()
    assert "start two `orchi-designer` subagents in Variant mode at once, one per engine" in design
    assert "each labelled by its idea, never by the skill that made it" in design
    assert "The variant the user picks sets the design engine for the project" in design
    assert "propose three to five of your own that fit the product" in design
    assert "`docs/design/references/`" in design and "`docs/design/surfaces/<surface>/`" in design
    assert "## Variant mode" in agent and "Name no favourite: the user chooses." in agent
    assert "build one variant on each of the three dealt themes" in agent
    assert "follow its workflow for a project without a stack (Phases 1 to 5)" in agent


def test_no_skill_reference_or_agent_still_names_impeccable():
    for path in sorted([*SKILLS.rglob("*"), *AGENTS.glob("*.agent.md")]):
        if path.is_file() and path.suffix in {".md", ".yml", ".html"} and "scripts" not in path.parts:
            assert "impeccable" not in read(path).lower(), path


def test_exploration_runs_a_design_session_before_converging():
    exploration, explore = reference("exploration"), skill("orchi-explore")
    assert exploration.index("4. **Design.**") < exploration.index("5. **Converge.**") < exploration.index("6. **Shape.**")
    for step in ("1. **Structure.**", "2. **Style.**", "3. **Engine round.**", "4. **The whole system.**"):
        assert step in exploration
    assert "`orchi-designer` in Wireframe mode builds three or four grey layouts of the screen" in exploration
    assert "propose five to seven strong references that fit the product's category" in exploration
    assert "start two `orchi-designer` subagents in Variant mode at once, one per design skill" in exploration
    assert "Start `orchi-designer` in Mockup mode" in exploration
    assert "Commit and push only what the user approved" in exploration
    assert "| Design | For a product with a user interface" in exploration
    assert "Research, Diverge, Design (the [design session](../orchi-core/references/exploration.md#design-session)" in explore
    assert "`orchi-designer` subagents in Wireframe, Variant, and Mockup modes for the design session" in explore
    assert "id: design" in form("exploration.yml")


def test_design_epic_and_planning_reuse_the_design_session():
    design, planning = skill("orchi-design"), reference("planning")
    assert "ran a design session (its Design section), copy what the user approved" in design
    assert "step 2 covers only the surfaces the session left out" in design
    assert "the design Epic names its Design section as its source" in planning
    assert "A design Epic without a design session behind it then agrees references with the user" in planning


def test_designer_wireframes_with_prototype_and_mocks_the_whole_system():
    agent = designer()
    for mode in ("## Wireframe mode", "## Variant mode", "## Mockup mode", "## Task mode", "## Audit mode"):
        assert mode in read(AGENTS / "orchi-designer.agent.md")
    assert "Follow prototype's workflow for a project without a stack (Phases 1 to 5) at wireframe fidelity: greys only" in agent
    assert "linked by the system's navigation, with an `index.html`" in agent
    assert "Wireframe, Variant, and Mockup modes write only in the output folder: no edits in the repository, no commits." in agent


def test_prototype_mode_interviews_through_a_living_prototype_and_keeps_every_later_phase():
    exploration, explore, agent = reference("exploration"), skill("orchi-explore"), designer()
    mode = exploration[exploration.index("## Prototype mode"):exploration.index("## Prototypes")]
    steps = ("1. **Interview.**", "2. **Variants.**", "3. **Living prototype.**", "4. **Before showing a change,**",
             "5. **Build it.**")
    assert [mode.index(step) for step in steps] == sorted(mode.index(step) for step in steps)
    assert "For an entirely new product, site, or interface built from scratch" in mode
    assert "The prototype is the interview's richest result, not a decision" in mode
    assert "Features, fixes, and redesigns of an existing product take the phases without prototype mode." in mode
    assert "Ask how many variants to build (three unless the user says otherwise)." in mode
    assert "never by the skill that made it" in mode
    assert "record its path in the Design section" in mode
    assert "After two failed repairs of the same thing, change the approach or ask the user" in mode
    assert "every idea the user raised and parked" in mode and "Then go on from phase 2." in mode
    assert "Picks and remarks are the user's alone, also in autonomous mode" in mode
    research = mode[mode.index("Research runs beside the interview"):mode.index("1. **Interview.**")]
    assert "start `orchi-researcher` subagents in Research mode in the background, several at once" in research
    for topic in ("the market and its competitors", "the domain", "products whose interfaces solve the same jobs"):
        assert topic in research
    assert "start `orchi-researcher` subagents on the market, the domain, and similar products" in explore
    assert "| Ideas | Every idea the user raised and parked" in exploration
    assert "id: ideas" in form("exploration.yml")
    assert "`Mode: prototype`" in explore and "keep interviewing while they work" in explore
    assert "report `<id> now researcher`" in explore and "take Orchi's `<id> remark:`" in explore
    assert "in prototype mode, a direction in one line instead" in agent
    assert "To change a mockup, copy it into the output folder and change only what the remarks name." in agent


def test_designer_runs_design_skill_scripts_from_its_worktree():
    agent = designer()
    assert "Run a skill's scripts from your worktree's root by their path" in agent
    assert "never from the skill's own directory" in agent and "`.hallmark/`" in agent
