import logging
from fastapi import APIRouter
from app.db.database import get_connection
from app.models.schemas import AgentCreate, HandoffCreate
from app.services.security import redact_secrets

router = APIRouter()

logger = logging.getLogger(__name__)

# -----------------------------
# CREATE AGENT
# -----------------------------
@router.post("/agents")
def create_agent(data: AgentCreate):
    redacted_payload = {
        "name": data.name,
        "prompt": redact_secrets(data.prompt),
        "type": data.type,
        "data_file": data.data_file,
    }
    logger.info(f"[CREATE AGENT] Incoming request: {redacted_payload}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO agents (name, prompt, type, data_file)
            VALUES (?, ?, ?, ?)
        """, (data.name, data.prompt, data.type, data.data_file))

        conn.commit()

        agent_id = cursor.lastrowid

        logger.info(f"[CREATE AGENT] Success - ID: {agent_id}, Name: {data.name}")

        return {
            "message": "Agent created",
            "id": agent_id
        }

    except Exception as e:
        logger.error(f"[CREATE AGENT] Failed - Error: {str(e)}", exc_info=True)
        return {"error": "Agent already exists or DB error"}

    finally:
        conn.close()
        logger.info("[CREATE AGENT] DB connection closed")


# -----------------------------
# EDIT AGENT
# -----------------------------
@router.put("/agents/{agent_id}")
def edit_agent(agent_id: int, data: AgentCreate):
    logger.info(
        f"[EDIT AGENT] Agent ID={agent_id} Incoming request: "
        f"{{'name': {data.name!r}, 'prompt': {redact_secrets(data.prompt)!r}, "
        f"'type': {data.type!r}, 'data_file': {data.data_file!r}}}"
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM agents WHERE id = ?", (agent_id,))
        existing = cursor.fetchone()
        if not existing:
            return {"error": "Agent not found"}

        cursor.execute(
            """
            UPDATE agents
            SET name = ?, prompt = ?, type = ?, data_file = ?
            WHERE id = ?
            """,
            (data.name, data.prompt, data.type, data.data_file, agent_id),
        )
        conn.commit()

        return {"message": "Agent updated", "id": agent_id}

    except Exception as e:
        logger.error(f"[EDIT AGENT] Failed - Error: {str(e)}", exc_info=True)
        return {"error": "Agent update failed"}

    finally:
        conn.close()
        logger.info("[EDIT AGENT] DB connection closed")


# -----------------------------
# LIST AGENTS
# -----------------------------
@router.get("/agents")
def list_agents():
    logger.info("[LIST AGENTS] Fetching all agents")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM agents")
        rows = cursor.fetchall()

        agents = [dict(row) for row in rows]

        logger.info(f"[LIST AGENTS] Retrieved {len(agents)} agents")

        return {"agents": agents}

    except Exception as e:
        logger.error(f"[LIST AGENTS] Failed - Error: {str(e)}", exc_info=True)
        return {"error": "Failed to fetch agents"}

    finally:
        conn.close()
        logger.info("[LIST AGENTS] DB connection closed")


# -----------------------------
# ADD HANDOFFS
# -----------------------------
@router.post("/agents/{agent_id}/handoffs")
def add_handoffs(agent_id: int, data: HandoffCreate):
    logger.info(f"[ADD HANDOFFS] Parent Agent: {agent_id}")
    logger.info(f"[ADD HANDOFFS] Children: {data.child_agent_ids}")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for child_id in data.child_agent_ids:
            logger.info(f"[ADD HANDOFFS] Linking {agent_id} -> {child_id}")

            cursor.execute("""
                INSERT INTO agent_handoffs (parent_agent_id, child_agent_id)
                VALUES (?, ?)
            """, (agent_id, child_id))

        conn.commit()

        logger.info(f"[ADD HANDOFFS] Success for parent {agent_id}")

        return {"message": "Handoffs added"}

    except Exception as e:
        logger.error(f"[ADD HANDOFFS] Failed - Error: {str(e)}", exc_info=True)
        return {"error": "Failed to add handoffs"}

    finally:
        conn.close()
        logger.info("[ADD HANDOFFS] DB connection closed")

# -----------------------------
# CLEAR DATABASE
# -----------------------------
@router.delete("/agents")
def clear_database():
    logger.warning("[CLEAR DATABASE] Deleting ALL agents and handoffs")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Delete all handoffs first
        cursor.execute("DELETE FROM agent_handoffs")

        # Delete all agents
        cursor.execute("DELETE FROM agents")

        conn.commit()

        logger.warning("[CLEAR DATABASE] All data deleted")

        return {"message": "All agents and handoffs deleted"}

    except Exception as e:
        logger.error(f"[CLEAR DATABASE] Failed - Error: {str(e)}", exc_info=True)
        return {"error": "Failed to clear database"}

    finally:
        conn.close()
        logger.info("[CLEAR DATABASE] DB connection closed")