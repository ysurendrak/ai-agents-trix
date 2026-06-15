from tools.boredtools import tools_schema as bored_tools_schema, tools as bored_tools

import logging
import json
import os
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BoredAgent(): 
    def __init__(self, tools_schema, tools):
        self.tools_schema = tools_schema
        self.tools = tools

    def run(self, prompt: str, tools: list = None):
        logger.info(f"Received prompt: {prompt}")
        logger.info(f"Available tools: {list(self.tools.keys())}")

        if tools is None:
            tools = self.tools_schema

        # 1. Plan: For simplicity, we will just call the first tool in the schema with the prompt as a parameter.
        logger.info(f"Planning tasks based on the prompt")
        plan_tasks = self.agent_plan(prompt)

        # 2. Execute the planned tasks sequentially
        logger.info(f"Executing planned tasks: {plan_tasks}")
        results = self.execute_tasks(plan_tasks)

        # 3. Create a final response based on the results of the executed tasks
        logger.info(f"Creating final response based on execution results")
        final_response = self.synthesize_response(prompt, results)
        logger.info(f"Final response: {final_response}")
        return final_response


    # Execute the planned tasks by asking the LLM
    def agent_plan(self, prompt):
        # For simplicity, we will just call the first tool in the schema with the prompt as a parameter.
        logger.info(f"Planning tasks based on the prompt")
        planner_system_prompt = (
            "You are a sophisticated planner Agent. "
            "Your job is to break down complex user questions into sequential, simple tasks. "
            "Return a JSON object with a single key  "
            " - 'tasks': list[string] #which contains a list of strings."
        )

        plan_tasks = self.ask_llm(planner_system_prompt, prompt, json_output=True)
        logger.info(f"Planned tasks: {plan_tasks}")
        return plan_tasks

    # Execute the planned tasks by asking the tools
    def execute_tasks(self, plan_tasks, tools:list):
        execution_results = []
        response = ""
        execution_system_prompt  = (
            "You are a sophisticated planner Agent. "
            "Your job is to find the correct given tools to the system to solve the given tasks."
            "The available tools and the task you will get from the user"
            "If no tools fit to Task write None"
            "Return a JSON object with a single key  "
            " - 'id: int #unique id to identify the task "
            " - 'task': {task}"
            " - 'function': string # name of the tool"
            " - 'properties: dict # properties to execute the function"
            " - 'dependencies': list # id's if the needed results of other tasks"
        )
        for task in plan_tasks.get("tasks", []):
            logger.info(f"Executing task: {task}")
            user_prompt = (f"I have the following task to do: {task}"  
                           f"I can use the following tools: {tools} to solve the taks "
                            "Tell me the correct tool to use for a given task"
                           f"Here is the full list of tasks {plan_tasks}"
                           F"Here are the executions that are already done {execution_results} take the results of tasks have dependencies."
            )
            response = self.ask_llm(execution_system_prompt, user_prompt, json_output=True)
            logger.info(f"Received response for task execution: {response}")
            kwargs = response["properties"]
            function_name = response["function"]
            if function_name in self.tools:
                looger.info(f"Executing tool '{function_name}' with properties: {kwargs}")
                result = self.tools[function_name](kwargs) # self.tools[function_name] means calling it like get_bored_activity_by_type(kwargs)
                logger.info(f"Result from tool '{function_name}': {result}")
                execution_results.append({
                    "id": response["id"],
                    "task": task,
                    "function": function_name,
                    "properties": kwargs,
                    "result": result
                })
            else:
                logger.warning(f"Tool '{function_name}' not found. Skipping task.")
                execution_results.append({
                    "id": response["id"],
                    "task": task,
                    "function": function_name,
                    "properties": kwargs,
                    "result": None
                })
        
        logger.info(f"All tasks executed. Final results: {execution_results}")
        return execution_results

    # Synthesize a final response based on the results of the executed tasks
    def synthesize_response(self, prompt, execution_results):
        synthesis_system_prompt = (
            "You are a helpful assistant. You have been given a user question"
            "and a set of execution results from various tools. "
            "Your goal is to provide a final, concise answer based on these results."
            "Check if the task of the user is fullfilled."
            "If not let him know that you don't have the tools to fullfill the tasks"
        )

        context = f"User question: {prompt}\n\nExecution results: {execution_results}"
        final_response = self.ask_llm(synthesis_system_prompt, context, json_output=False)
        logger.info(f"Synthesized final response: {final_response}")
        return final_response

    @staticmethod
    def ask_llm(system_prompt, user_prompt, model_name="llama3.2", json_output=False):
        if json_output:
            response_format = "json"
        else:
            response_format = "text"
        
        try:
            response = ollama.chat(
                model=model_name,
                # Enabling JSON mode forces the model to return valid JSON syntax
                format=response_format,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            if json_output:
                logger.info(f"Received JSON response from the model: {response}")
                # The response text string is stored in ['message']['content']
                raw_json_string = response["message"]["content"]

                # Parse the string into a native Python dictionary
                return json.loads(raw_json_string)
            else:
                logger.info(f"Received text response from the model: {response}")
                return response["message"]["content"]

        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from the model. Response was: " + raw_json_string)
            return {}
        except Exception as e:
            logger.error(f"An error occurred while calling the LLM: {e}")
            return {}  
        
if OLLAMA_API:
    # Initialize the BoredAgent with the tools schema and tools
    bored_agent = BoredAgent(tools_schema=bored_tools_schema, tools=bored_tools)
    result = bored_agent.run(prompt="I'm feeling bored. What can I do to relax?")
    logger.info(f"Agent result: {result}")
else:
    logger.warning("OLLAMA_API is not available. BoredAgent will not be initialized.")