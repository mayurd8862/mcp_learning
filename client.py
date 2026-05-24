import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ---------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------------------------------
# Gemini Client
# ---------------------------------------------------

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------
# MCP Server Parameters
# ---------------------------------------------------

server_params = StdioServerParameters(
    command="python",
    args=[
        r"C:\Users\mayur\Desktop\NEW Chapter\MCP\mcp_learning\mcp_server.py"
    ],
)

# ---------------------------------------------------
# Main Function
# ---------------------------------------------------

async def main():

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize MCP session
            await session.initialize()

            # Get available MCP tools
            tools_result = await session.list_tools()

            print("\nAvailable MCP Tools:\n")

            for tool in tools_result.tools:
                print(f"- {tool.name}")

            print("\nMCP Connected Successfully!\n")

            while True:

                user_query = input("\nYou: ")

                if user_query.lower() == "exit":
                    break

                # Convert MCP tools for Gemini
                gemini_tools = []

                for tool in tools_result.tools:

                    gemini_tools.append(
                        types.Tool(
                            function_declarations=[
                                {
                                    "name": tool.name,
                                    "description": tool.description,
                                    "parameters": tool.inputSchema,
                                }
                            ]
                        )
                    )

                # Send query to Gemini
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=user_query,
                    config=types.GenerateContentConfig(
                        tools=gemini_tools
                    ),
                )

                candidate = response.candidates[0]

                parts = candidate.content.parts

                final_response = []

                for part in parts:

                    # ---------------------------------------------------
                    # Tool Calling
                    # ---------------------------------------------------

                    if hasattr(part, "function_call") and part.function_call:

                        tool_name = part.function_call.name
                        tool_args = dict(part.function_call.args)

                        print(f"\nCalling Tool: {tool_name}")
                        print(f"Arguments: {tool_args}")

                        # Execute MCP Tool
                        tool_result = await session.call_tool(
                            tool_name,
                            tool_args,
                        )

                        result_text = str(tool_result.content)

                        # Send tool result back to Gemini
                        second_response = client.models.generate_content(
                            model="gemini-3.1-flash-lite",
                            contents=[
                                user_query,
                                f"Tool Result: {result_text}",
                            ],
                        )

                        final_response.append(
                            second_response.text
                        )

                    else:
                        if hasattr(part, "text"):
                            final_response.append(part.text)

                print("\nAssistant:")
                print("\n".join(final_response))


# ---------------------------------------------------
# Run Client
# ---------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())