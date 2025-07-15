# Create a new file: utils/assistant_manager.py
import openai
import time
import json
from flask import current_app




# Try importing - if it fails, we'll define it inline
try:
    from utils.standalone_assistant_manager import StandaloneAssistantManager
except ImportError:
    print("Import failed, defining StandaloneAssistantManager inline...")
    
    import openai
    import time
    import json
    
    class StandaloneAssistantManager:
        def __init__(self, api_key, assistant_id, thread_id):
            self.client = openai.OpenAI(api_key=api_key)
            self.assistant_id = assistant_id
            self.thread_id = thread_id

        def add_message_to_thread(self, role, message):
            print(f'Adding message to thread: {role}, {message}')
            return self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role=role,
                content=message,
            )
        
        def run_assistant(self, message):
            print(f'Running assistant with message: {message}')
            
            # Add user message to thread
            self.add_message_to_thread("user", message)

            # Create run
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
            )
            
            # Wait for completion
            run = self.wait_for_update(run)

            if run.status == "failed":
                print('Run failed')
                return None
            elif run.status == "requires_action":
                print(f'Run requires action')
                return self.handle_require_action(run)
            else:
                print('Run completed')
                return self.get_last_assistant_message()
            
        def wait_for_update(self, run):
            while run.status in ["queued", "in_progress"]:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id,
                )
                time.sleep(1)
                print(f"Run status: {run.status}")

            return run
        
        def get_last_assistant_message(self):
            print('Getting last assistant message')
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            
            if messages.data and messages.data[0].role == 'assistant':
                message = messages.data[0]
                for content_block in message.content:
                    if content_block.type == 'text':
                        return content_block.text.value
            
            return None
            
        def handle_require_action(self, run):
            print('Handling required action - returning simple response')
            # For now, just return a simple message if tools are required
            return "This assistant requires tools that aren't implemented yet."