from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool
def greet(name: str) -> str:
    """Greet a person by name"""
    return f"Hello {name}!"


@mcp.prompt
def welcome_message(name: str) -> str:
    """Generate a welcome message for a person by name"""
    return f"Welcome to FastMCP, {name}! We're excited to have you here."


@mcp.resource('calendar://events/{date}')
def get_calendar_events(date: str):
    """Fetch calendar events for a specific date"""
    # Simulated calendar events
    events = {
        "2024-01-01": ["New Year's Day Celebration", "Brunch with Friends"],
        "2024-02-14": ["Valentine's Day Dinner", "Movie Night"],
        "2024-03-17": ["St. Patrick's Day Parade", "Family Gathering"]
    }
    return events.get(date, ["No events found for this date"])


@mcp.resource("data://config")
def get_config(): return {"version": 1}


if __name__ == "__main__":
    mcp.run()
