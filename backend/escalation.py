import uuid
from datetime import datetime
from typing import Optional

ESCALATION_TRIGGERS = [
    "human", "agent", "person", "speak to someone",
    "talk to someone", "real person", "live agent",
    "escalate", "manager", "supervisor", "not helpful",
    "useless", "frustrated", "not working", "human agent"
]


class EscalationManager:

    def __init__(self):
        self.tickets = {}

    def user_wants_human(self, message: str) -> bool:
        msg_lower = message.lower()
        return any(trigger in msg_lower for trigger in ESCALATION_TRIGGERS)

    def create_ticket(self, session_id: str, user_message: str, reason: str, bot_answer: Optional[str] = None) -> dict:
        ticket_id = f"TICKET-{str(uuid.uuid4())[:8].upper()}"
        ticket = {
            "id": ticket_id,
            "session_id": session_id,
            "user_message": user_message,
            "escalation_reason": reason,
            "bot_answer": bot_answer,
            "status": "open",
            "priority": "high" if "user requested" in reason.lower() else "medium",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "assigned_to": None,
        }
        self.tickets[ticket_id] = ticket
        print(f"[ESCALATION] Ticket: {ticket_id} | Reason: {reason}")
        return ticket

    def get_all_tickets(self) -> list:
        return sorted(self.tickets.values(), key=lambda t: t["created_at"], reverse=True)