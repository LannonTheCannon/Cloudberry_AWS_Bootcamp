import openai
import time
import json

class StandaloneAssistantManager:
    def __init__(self, api_key, assistant_id, thread_id=None):
        self.client = openai.OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        
        # 🔥 Create new thread if none provided
        if thread_id is None:
            thread = self.client.beta.threads.create()
            self.thread_id = thread.id
            print(f"🔥 Created new thread: {self.thread_id}")
        else:
            self.thread_id = thread_id
            print(f"🔥 Using existing thread: {self.thread_id}")
    
    def add_message_to_thread(self, role, message):
        if not self.thread_id:
            raise ValueError("No thread_id available")
            
        return self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role=role,
            content=message,
        )
    
    def run_assistant(self, message):
        try:
            print(f"Running assistant with message: {message}")
            print(f"Thread ID: {self.thread_id}")
            
            # Add user message
            self.add_message_to_thread("user", message)
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id
            )
            
            # Wait for completion
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Get messages
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id
                )
                
                # Return the latest assistant message
                for message in messages.data:
                    if message.role == 'assistant':
                        return message.content[0].text.value
                        
            else:
                print(f"Run failed with status: {run.status}")
                return None
                
        except Exception as e:
            print(f"Error in run_assistant: {e}")
            import traceback
            traceback.print_exc()
            return None