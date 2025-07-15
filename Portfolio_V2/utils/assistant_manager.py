# Create a new file: utils/assistant_manager.py
import openai
import time
import json
from flask import current_app

class AssistantManager:
    def __init__(self, api_key, assistant_id, thread_id):
        self.openAI = openai.OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.thread_id = thread_id
        
        # Load existing assistant and thread
        self.assistant = self.openAI.beta.assistants.retrieve(assistant_id)
        self.thread = self.openAI.beta.threads.retrieve(thread_id)

    def add_message_to_thread(self, role, message):
        current_app.logger.info(f'Adding message to thread: {role}, {message}')
        return self.openAI.beta.threads.messages.create(
            thread_id=self.thread_id,
            role=role,
            content=message,
        )
    
    def run_assistant(self, message):
        current_app.logger.info(f'Running assistant: {message}')
        message = self.add_message_to_thread("user", message)

        run = self.openAI.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
        )
        run = self.wait_for_update(run)

        if run.status == "failed":
            current_app.logger.info('Run failed')
            return None
        elif run.status == "requires_action":
            current_app.logger.info(f'Run requires action: {run}')
            return self.handle_require_action(run)
        else:
            current_app.logger.info('Run completed')
            return self.get_last_assistant_message()
        
    def handle_require_action(self, run):
        current_app.logger.info('Handling required action')
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        tool_outputs = self.generate_tool_outputs(tool_calls)

        run = self.openAI.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
        
        run = self.wait_for_update(run)

        if run.status == "failed":
            current_app.logger.info('Run failed')
            return None
        elif run.status == "completed":
            return self.get_last_assistant_message()
        
    def wait_for_update(self, run):
        while run.status in ["queued", "in_progress"]:
            run = self.openAI.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id,
            )
            time.sleep(1)
            current_app.logger.info(f"Run status: {run.status}")

        return run
    
    def get_last_assistant_message(self):
        current_app.logger.info('Getting last assistant message')
        messages = self.openAI.beta.threads.messages.list(thread_id=self.thread_id)
        if messages.data and messages.data[0].role == 'assistant':
            message = messages.data[0]
            for content_block in message.content:
                if content_block.type == 'text':
                    return content_block.text.value
        return None
        
    def generate_tool_outputs(self, tool_calls):
        current_app.logger.info('Generating tool outputs')
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            tool_call_id = tool_call.id

            args_dict = json.loads(arguments)

            if hasattr(self, function_name):
                function_to_call = getattr(self, function_name)
                output = function_to_call(**args_dict) 

                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": output,
                })

        return tool_outputs