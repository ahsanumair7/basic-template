import asyncio
import json
import os
from src.agent.capability import MatchingCapability
from src.main import AgentWorker
from src.agent.capability_worker import CapabilityWorker

INTRO_PROMPT = "Hi! I'm your daily life advisor. Please tell me about a problem you're facing."
FEEDBACK_PROMPT = "Are you satisfied with the advice?"

class DailyLifeAdvisorCapability(MatchingCapability):
    worker: AgentWorker = None
    capability_worker: CapabilityWorker = None

    @classmethod
    def register_capability(cls) -> "MatchingCapability":
        with open(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
        ) as file:
            data = json.load(file)
        return cls(
            unique_name=data["unique_name"],
            matching_hotwords=data["matching_hotwords"],
        )

    async def give_advice(self):
        """
        The main function for giving advice to the user.
        It asks the user about their problem, provides a solution, and asks for feedback.

        - `run_io_loop`: Combines speaking and recording user responses. It asks the user a question and waits for their answer.
        - `speak`: Reads aloud a message, like the advice given to the user.
        - `user_response`: Records what the user says or types as feedback on the advice.
        """

        # Introduce the advisor and ask for the user's problem
        user_problem = await self.capability_worker.run_io_loop(INTRO_PROMPT)

        # Generate a solution based on the problem
        solution_prompt = f"The user has the following problem: {user_problem}. Provide a helpful solution in just 1 or 2 sentences."
        solution = self.capability_worker.text_to_text_response(solution_prompt)

        # Speak the solution and ask if the user is satisfied
        solution_with_feedback = solution + FEEDBACK_PROMPT
        await self.capability_worker.speak(solution_with_feedback)

        self.worker.user_is_finished_speak_event.set()
        self.worker.use_final_transcript_event.set()
        
        # Get the user's feedback
        user_feedback = await self.capability_worker.user_response()
        self.worker.editor_logging_handler.info(f"User feedback: {user_feedback}")

        self.worker.use_final_transcript_event.clear()

        # Resume the normal workflow
        self.capability_worker.resume_normal_flow()

    def call(self, worker: AgentWorker):
        # Initialize the worker and capability worker
        self.worker = worker
        self.capability_worker = CapabilityWorker(self.worker)

        # Trigger the capability event
        self.worker.capability_event.set()

        # Start the advisor functionality
        asyncio.create_task(self.give_advice())
