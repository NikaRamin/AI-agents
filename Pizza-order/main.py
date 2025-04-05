from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.tool import ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from collections.abc import Iterable
from random import randint
import gradio as gr

load_dotenv()

# Configure Google API key
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError(
        "GOOGLE_API_KEY not found in environment variables. "
        "Please copy .env.example to .env and add your API key."
    )

# Initialize LLM with proper configuration
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.7,
    )
except Exception as e:
    print(f"Error initializing LLM: {e}")
    print("Please make sure your GOOGLE_API_KEY is valid")
    exit(1)

class PizzaOrderState(TypedDict):
    messages: Annotated[list, add_messages]
    order: list[str]
    finished: bool
    confirmed: bool  
    order_placed: bool  

PIZZABOT_SYSINT = {
    "role": "system",
    "content": """
    role: You are PizzaBot, a friendly pizza ordering assistant. Always be conversational and natural.
    
    Key behaviors:
    1. Never show function calls or technical details
    2. Use natural dialogue for order flow:
       - Taking order: "Would you like any toppings with that?"
       - Confirming: "Here's what I have: [order]. Would you like to confirm?"
       - Placing: "Great! Your order will be ready in 20-30 minutes."
       - Adding: "I've added that to your order."
       - Checking: "Here's what you have so far:"
    3. When showing prices:
       - Small: $10, Medium: $12, Large: $15, Extra Large: $18
       - Each topping: +$1.50
       - Stuffed crust: +$2.00
    4. Guide customers through size -> toppings -> crust naturally
    5. We have no delivary and only take orders for pickup.
    """
}

WELCOME_MSG = "Welcome to you favorite pizzeria! Type `q` to quit. What kind of pizza can I get started for you today?"

@tool
def get_menu() -> str:
    """Get the current pizza menu with all available options."""
    return """
    MENU:
    
    Pizzas (Base prices: S-$10, M-$12, L-$15, XL-$18):
    - Margherita: Tomato sauce, mozzarella, basil
    - Pepperoni: Tomato sauce, mozzarella, pepperoni
    - Hawaiian: Tomato sauce, mozzarella, ham, pineapple
    - Vegetarian: Tomato sauce, mozzarella, mushrooms, peppers, onions
    - Supreme: Tomato sauce, mozzarella, pepperoni, sausage, mushrooms, peppers, onions (+$2)
    
    Extra Toppings (+$1.50 each):
    - Meats: Pepperoni, Sausage, Ham, Bacon
    - Veggies: Mushrooms, Peppers, Onions, Olives, Tomatoes
    - Others: Extra cheese, Pineapple, Basil
    
    Sizes:
    - Small (10"): $10
    - Medium (12"): $12
    - Large (14"): $15
    - Extra Large (16"): $18
    
    Crust Options:
    - Regular: Included
    - Thin: Included
    - Thick: +$1
    - Stuffed: +$2
    """

@tool
def add_to_order(pizza: str, size: str, crust: str, extra_toppings: Iterable[str]) -> str:
    """
    Add a pizza to the current order.
    """
    # This function is a placeholder – actual order update happens in order_node.
    pass

@tool
def confirm_order() -> str:
    """
    Display the current order to the customer and ask for confirmation.
    """
    pass

@tool
def get_order() -> str:
    """
    Retrieve the current order contents.
    """
    pass

@tool
def clear_order() -> None:
    """
    Remove all items from the current order.
    """
    pass

@tool
def place_order() -> int:
    """
    Submit the order to the kitchen for preparation.
    """
    pass

def order_node(state: PizzaOrderState) -> PizzaOrderState:
    """
    Handles order-related operations. Process only unhandled tool calls and mark them as processed.
    """
    tool_msg = state.get("messages", [])[-1]
    order = state.get("order", [])
    outbound_msgs = []
    order_placed = state.get("order_placed", False)

    # Get tool calls if present
    tool_calls = getattr(tool_msg, "tool_calls", [])
    for tool_call in tool_calls:
        # Only process tool calls that haven't been handled yet
        if not tool_call.get("processed", False):
            if tool_call["name"] == "add_to_order":
                pizza = tool_call["args"]["pizza"]
                size = tool_call["args"]["size"]
                crust = tool_call["args"]["crust"]
                extra_toppings = tool_call["args"]["extra_toppings"]
                toppings_str = ", ".join(extra_toppings) if extra_toppings else "no extra toppings"
                order.append(f"{size} {pizza} ({crust}, {toppings_str})")
                response = "\n".join(order)

            elif tool_call["name"] == "confirm_order":
                print("Your order:")
                if not order:
                    print("  (no items)")
                for item in order:
                    print(f"  {item}")
                response = input("Is this correct? ")

            elif tool_call["name"] == "get_order":
                response = "\n".join(order) if order else "(no order)"

            elif tool_call["name"] == "clear_order":
                order.clear()
                response = "Order cleared."

            elif tool_call["name"] == "place_order":
                print("Sending order to kitchen!")
                print("\n".join(order))
                order_placed = True
                response = randint(10, 30)  # ETA in minutes

            else:
                raise NotImplementedError(f'Unknown tool call: {tool_call["name"]}')

            # Mark this tool call as processed to avoid reprocessing later
            tool_call["processed"] = True

            outbound_msgs.append(
                ToolMessage(
                    content=response,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

   
    if hasattr(tool_msg, "tool_calls"):
        tool_msg.tool_calls = tool_calls

   
    state["messages"].append(AIMessage(content="Processed tool calls.", tool_calls=[]))
    state["order"] = order
    state["order_placed"] = order_placed
    return state

def route_to_tools(state: PizzaOrderState) -> str:
    """
    Routes between chat and tool nodes. Only routes to tools if there are unprocessed tool calls.
    """
    if not (msgs := state.get("messages", [])):
        raise ValueError(f"No messages found when parsing state: {state}")
    msg = msgs[-1]

    # Route to tools only if there are new, unprocessed tool calls
    if hasattr(msg, "tool_calls") and any(not tc.get("processed", False) for tc in msg.tool_calls):
        return "tools"
    elif state.get("finished", False):
        return END
    else:
        return "human"

def human_node(state: PizzaOrderState) -> PizzaOrderState:
    """
    Handles human input. Clears previous tool calls from the last message to prevent loops.
    """
    last_msg = state["messages"][-1]
    print("Model:", last_msg.content)
    user_input = input("User: ")
    if user_input in {"q", "quit", "exit", "goodbye"}:
        state["finished"] = True
    else:
        # Clear any tool_calls on the last message
        if hasattr(last_msg, "tool_calls"):
            last_msg.tool_calls = []
        state["messages"].append({"role": "user", "content": user_input})
    return state

def clean_llm_response(content: str) -> str:
    """Remove tool calls from LLM responses and replace with natural language."""
    replacements = {
        "confirm_order()": "Would you like to confirm your order?",
        "place_order()": "Great! Your order has been placed and will be delivered in 20-30 minutes.",
        "get_order()": "Here's what you have in your order:",
        "clear_order()": "I've cleared your order.",
        "add_to_order": "I'll add that to your order.",
        "ok": "",
        "\n\n": "\n", 
    }
    
    for tool_call, natural_text in replacements.items():
        if tool_call in content:
            content = content.replace(tool_call, natural_text)
    
    return content.strip()

def create_chat_interface():
    """Creates and returns the Gradio chat interface."""
    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label="PizzaBot")
        with gr.Row(equal_height=True):
            msg = gr.Textbox(label="Message", placeholder="Type your message here...", scale=4)
            with gr.Row(equal_height=True):
                submit = gr.Button("Send", scale=1)
                clear = gr.Button("Clear", scale=1)
            
        state = gr.State({
            "messages": [], 
            "order": [], 
            "finished": False,
            "confirmed": False,
            "order_placed": False
        })
        
        def handle_order_confirmation(message: str, state: dict) -> tuple[str, bool]:
            """Handle order confirmation responses"""
            if "yes" in message.lower() or "correct" in message.lower():
                state["confirmed"] = True
                return "Great! Shall I place your order now?", True
            elif "no" in message.lower():
                state["confirmed"] = False
                return "What would you like to change about your order?", False
            return None, False

        def user_message(message, history, state):
            """Handle user messages through Gradio interface."""
            if not message.strip():
                return "", history, state

            
            history = history if history is not None else []

            # Handle exit commands
            if message.strip() in {"q", "quit", "exit", "goodbye"}:
                state["finished"] = True
                history.append((message, "Goodbye! Thank you for ordering!"))
                return "", history, state

            # Handle confirmation responses
            if state["order"] and not state["confirmed"]:
                if "yes" in message.lower():
                    state["confirmed"] = True
                    response = "Great! Your order is confirmed. Would you like me to place the order now?"
                elif "no" in message.lower():
                    response = "What would you like to change about your order?"
                else:
                    response = "Please respond with 'yes' or 'no' to confirm your order."
                history.append((message, response))
                state["messages"].append({"role": "user", "content": message})
                state["messages"].append({"role": "assistant", "content": response})
                return "", history, state

            # Handle placing the order
            if state["confirmed"] and not state["order_placed"]:
                if "yes" in message.lower():
                    state["order_placed"] = True
                    response = "Placing your order now... Your order will arrive in 20-30 minutes."
                elif "no" in message.lower():
                    response = "Let me know when you're ready to place the order."
                else:
                    response = "Please respond with 'yes' or 'no' to place your order."
                history.append((message, response))
                state["messages"].append({"role": "user", "content": message})
                state["messages"].append({"role": "assistant", "content": response})
                return "", history, state

            # Add user message to state
            state["messages"].append({"role": "user", "content": message})

            # Get LLM response
            messages = [PIZZABOT_SYSINT] + state["messages"]
            response = llm.invoke(messages)
            content = clean_llm_response(response.content)

            # Handle order already placed
            if state["order_placed"]:
                content = "Your order has already been placed. Start a new order?"

            # Update history and state with proper tuple format
            history.append((message, content))
            state["messages"].append({"role": "assistant", "content": content})
            
            return "", history, state

        
        submit.click(user_message, [msg, chatbot, state], [msg, chatbot, state])
        msg.submit(user_message, [msg, chatbot, state], [msg, chatbot, state])
        clear.click(
            lambda: (None, [], {
                "messages": [], 
                "order": [], 
                "finished": False,
                "confirmed": False,
                "order_placed": False
            }), 
            None, 
            [msg, chatbot, state], 
            queue=False
        )

    return demo

if __name__ == "__main__":
    demo = create_chat_interface()
    demo.launch(share=True)

