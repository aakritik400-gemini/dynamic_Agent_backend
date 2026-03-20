import logging
import uuid

from agents import Agent
from app.db.database import get_connection
from app.services.file_loader import load_txt_data
from app.core.config import model

logger = logging.getLogger(__name__)


def build_agent(
    agent_id: int,
    request_id: str = None,
    visited=None,
    cache=None
):

    if request_id is None:
        request_id = str(uuid.uuid4())

    if visited is None:
        visited = set()

    if cache is None:
        cache = {}

    logger.info(f"[{request_id}] [BUILD AGENT] Start -> ID: {agent_id}")

    # -----------------------------
    # CACHE HIT 
    # -----------------------------
    if agent_id in cache:
        logger.info(f"[{request_id}] Cache hit for agent {agent_id}")
        return cache[agent_id]

    # -----------------------------
    # Prevent circular recursion
    # -----------------------------
    if agent_id in visited:
        logger.warning(f"[{request_id}] Circular dependency detected: {agent_id}")
        return None

    visited.add(agent_id)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
        agent = cursor.fetchone()

        if not agent:
            logger.warning(f"[{request_id}] Agent not found: {agent_id}")
            return None

        logger.info(f"[{request_id}] Loaded agent: {agent['name']} ({agent['type']})")

        prompt = agent["prompt"]

        # -----------------------------
        # File injection
        # -----------------------------
        if agent["data_file"]:
            logger.info(f"[{request_id}] Loading file: {agent['data_file']}")
            data = load_txt_data(agent["data_file"])

            if data:
                prompt += f"\n\nDATA:\n{data}"
                logger.info(f"[{request_id}] File injected ({len(data)} chars)")
            else:
                logger.warning(f"[{request_id}] File empty")

        handoffs = []

        # -----------------------------
        # Super agent recursion
        # -----------------------------
        if agent["type"] == "super":
            logger.info(f"[{request_id}] Fetching handoffs for {agent_id}")

            cursor.execute("""
                SELECT child_agent_id FROM agent_handoffs
                WHERE parent_agent_id = ?
            """, (agent_id,))

            children = cursor.fetchall()

            for child in children:
                child_id = child["child_agent_id"]

                logger.info(f"[{request_id}] → Building child {child_id}")

                child_agent = build_agent(
                    child_id,
                    request_id=request_id,
                    visited=visited,
                    cache=cache
                )

                if child_agent:
                    handoffs.append(child_agent)

        # -----------------------------
        # Create Agent
        # -----------------------------
        built_agent = Agent(
        name=agent["name"],
        instructions=prompt,
        handoffs=handoffs,
        model=model
)

        setattr(built_agent, "agent_id", agent["id"])
             

        # -----------------------------
        # STORE IN CACHE ✅
        # -----------------------------
        cache[agent_id] = built_agent
        
        logger.info(f"[{request_id}] Agent built successfully: {agent['name']}")

        return built_agent

    except Exception as e:
        logger.error(
            f"[{request_id}] BUILD FAILED {agent_id}: {str(e)}",
            exc_info=True
        )
        return None

    finally:
        conn.close()
        logger.info(f"[{request_id}] DB closed for {agent_id}")