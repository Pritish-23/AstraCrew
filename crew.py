"""
AstraCrew: Multi-Agent Hierarchical Red-Teaming Crew
"""
import os
from pathlib import Path
import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.probe_tools import (
    execute_security_probe,
    list_available_probes,
    query_target_direct,
)


@CrewBase
class AstraRedTeamCrew:
    """AstraCrew Red-Teaming Hierarchical Orchestrator."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ---------------------------------------------------------
    # AGENTS
    # ---------------------------------------------------------

    @agent
    def lead_director(self) -> Agent:
        return Agent(
            config=self.agents_config["lead_director"],
            tools=[list_available_probes, execute_security_probe, query_target_direct],
            verbose=True,
            memory=False,
        )

    @agent
    def infiltration_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["infiltration_specialist"],
            tools=[execute_security_probe, query_target_direct],
            verbose=True,
            memory=False,
        )

    @agent
    def obfuscation_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["obfuscation_analyst"],
            tools=[execute_security_probe, query_target_direct],
            verbose=True,
            memory=False,
        )

    @agent
    def cognitive_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config["cognitive_specialist"],
            tools=[execute_security_probe, query_target_direct],
            verbose=True,
            memory=False,
        )

    # ---------------------------------------------------------
    # TASKS
    # ---------------------------------------------------------

    @task
    def coordinate_redteam_campaign(self) -> Task:
        return Task(
            config=self.tasks_config["coordinate_redteam_campaign"],
        )

    @task
    def execute_infiltration_probes(self) -> Task:
        return Task(
            config=self.tasks_config["execute_infiltration_probes"],
        )

    @task
    def execute_obfuscation_probes(self) -> Task:
        return Task(
            config=self.tasks_config["execute_obfuscation_probes"],
        )

    @task
    def execute_cognitive_probes(self) -> Task:
        return Task(
            config=self.tasks_config["execute_cognitive_probes"],
        )

    # ---------------------------------------------------------
    # CREW PIPELINE
    # ---------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """Assembles the agents and tasks into a hierarchical red team."""
        offensive_specialists = [
            self.infiltration_specialist(),
            self.obfuscation_analyst(),
            self.cognitive_specialist(),
        ]
        
        assigned_tasks = [
            self.coordinate_redteam_campaign(),
            self.execute_infiltration_probes(),
            self.execute_obfuscation_probes(),
            self.execute_cognitive_probes(),
        ]

        return Crew(
            agents=offensive_specialists,
            tasks=assigned_tasks,
            process=Process.hierarchical,
            manager_agent=self.lead_director(),
            verbose=True,
        )