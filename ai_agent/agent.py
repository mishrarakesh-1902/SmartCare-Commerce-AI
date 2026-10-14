import os
import json
import uuid
import time
import logging
import datetime
from typing import Dict, Any, Optional

from .retriever import search_ecommerce_docs

logger = logging.getLogger(__name__)

MODEL_NAME = "llama3.2"

class ECommerceSupportAgent:
    """
    Autonomous AI Customer Support & Operations Agent for Ajara Shopper.
    Combines Database Tool Calling (Order Lookup), Semantic RAG,
    Deterministic Guardrails, and Grounded Response Generation.
    """

    def _lookup_order(self, order_id: str, user=None) -> Optional[Dict[str, Any]]:
        """
        Tool: Looks up live customer order details directly from the Django database.
        """
        if not order_id:
            return None

        # Clean order id if prefixed with '#'
        clean_id = str(order_id).replace("#", "").strip()

        try:
            from app.models import Order
            # Try lookup by pk / id
            order = None
            if clean_id.isdigit():
                order = Order.objects.filter(id=int(clean_id)).first()

            if not order and user and user.is_authenticated:
                order = Order.objects.filter(user=user).order_by('-id').first()

            if order:
                order_date = order.date
                if isinstance(order_date, datetime.datetime):
                    order_date = order_date.date()
                elif not isinstance(order_date, datetime.date):
                    order_date = datetime.date.today()

                days_elapsed = (datetime.date.today() - order_date).days

                return {
                    "id": order.id,
                    "product": order.product,
                    "price": order.price,
                    "quantity": order.quantity,
                    "total": order.total,
                    "address": order.address,
                    "phone": order.phone,
                    "date": order_date.strftime("%Y-%m-%d"),
                    "days_ago": days_elapsed,
                    "is_eligible_for_return": days_elapsed <= 7
                }
        except Exception as e:
            logger.warning(f"Order lookup error: {e}")
        return None

    def _classify_intent(self, subject: str, message: str) -> Dict[str, Any]:
        """
        Zero-shot classification of customer issue using Llama 3.2.
        """
        prompt = f"""You are a Customer Support Triage Specialist for an Indian E-commerce company (Ajara Shopper).
Analyze this customer inquiry and return ONLY a valid JSON object.

Schema:
{{
  "category": "return_or_exchange | refund_request | order_tracking | damaged_defective | order_cancellation | payment_issue | general_inquiry | spam",
  "urgency": "low | medium | high | critical",
  "sentiment": "positive | neutral | frustrated | angry",
  "reasoning": "One brief sentence explaining the classification"
}}

Rules:
- High/Critical: System failures, duplicate debits, extreme customer anger, legal mentions, or damaged goods.
- If asking where an order is: category must be 'order_tracking'.
- If asking for money back or cancellation: 'refund_request' or 'order_cancellation'.

Inquiry:
Subject: {subject}
Message: {message}

JSON Output:"""

        try:
            import ollama
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                format="json",
                options={"temperature": 0}
            )
            return json.loads(response['message']['content'])
        except Exception as e:
            logger.warning(f"Ollama classification fallback triggered: {e}")
            # Heuristic fallback
            msg_lower = (subject + " " + message).lower()
            if any(w in msg_lower for w in ["refund", "money back", "deducted"]):
                return {"category": "refund_request", "urgency": "high", "sentiment": "frustrated", "reasoning": "Keywords matched refund"}
            if any(w in msg_lower for w in ["return", "exchange", "replace", "size"]):
                return {"category": "return_or_exchange", "urgency": "medium", "sentiment": "neutral", "reasoning": "Keywords matched return/exchange"}
            if any(w in msg_lower for w in ["track", "where is", "delivery", "status"]):
                return {"category": "order_tracking", "urgency": "medium", "sentiment": "neutral", "reasoning": "Keywords matched order tracking"}
            if any(w in msg_lower for w in ["broken", "damaged", "tear", "defective"]):
                return {"category": "damaged_defective", "urgency": "high", "sentiment": "frustrated", "reasoning": "Keywords matched damaged goods"}
            return {"category": "general_inquiry", "urgency": "medium", "sentiment": "neutral", "reasoning": "General support inquiry"}

    def _determine_action(self, classification: Dict, message: str, order_info: Optional[Dict]) -> str:
        """
        Deterministic Guardrails: Evaluates business policies and safety constraints.
        """
        category = classification.get("category", "")
        urgency = classification.get("urgency", "medium")
        sentiment = classification.get("sentiment", "neutral")
        msg_lower = message.lower()

        # Priority 1: High Risk & Legal Threats
        critical_keywords = ["lawsuit", "sue", "legal action", "consumer forum", "fraud", "scam"]
        if any(word in msg_lower for word in critical_keywords):
            return "escalate_human"

        if urgency == "critical" or (urgency == "high" and sentiment == "angry"):
            return "escalate_human"

        # Priority 2: Damaged / Defective
        if category == "damaged_defective":
            return "instant_replacement_or_refund"

        # Priority 3: Return Eligibility Check
        if category in ["return_or_exchange", "refund_request"]:
            if order_info and not order_info.get("is_eligible_for_return"):
                return "return_window_expired_manager_review"
            return "process_return_approval"

        # Priority 4: Order Tracking
        if category == "order_tracking":
            return "provide_tracking_update"

        if category == "order_cancellation":
            return "process_order_cancellation"

        if category == "spam":
            return "close_spam"

        return "automated_resolution"

    def _generate_response(
        self,
        customer_name: str,
        subject: str,
        message: str,
        classification: Dict,
        action: str,
        retrieved_docs: list,
        order_info: Optional[Dict]
    ) -> str:
        """
        Synthesizes a grounded, human-grade support response.
        """
        order_str = "No specific order selected."
        if order_info:
            order_str = (
                f"Order ID: #{order_info['id']} | Product: {order_info['product']} | "
                f"Amount: ₹{order_info['price']} | Date: {order_info['date']} "
                f"({order_info['days_ago']} days ago, Return Eligible: {order_info['is_eligible_for_return']})"
            )

        context_str = "\n\n".join([f"[{d['filename']}]\n{d['content']}" for d in retrieved_docs])

        system_prompt = f"""You are Priya, a Senior Customer Success Specialist at Ajara Shopper.
Write a warm, empathetic, clear, and professional customer resolution email.

Customer Name: {customer_name or 'Valued Customer'}
Customer Order: {order_str}
Action To Execute: {action}
Store Policies Context:
{context_str}

CRITICAL RULES:
1. Address the customer respectfully by name.
2. If order details are present, mention the specific product and order ID so the customer knows you checked their account.
3. If an action is 'process_return_approval', confirm that their return is approved under our 7-day policy and tell them our courier partner will pick it up in 24-48 hours.
4. If an action is 'instant_replacement_or_refund', express deep apology for the defective/damaged item and confirm we are expediting a free replacement.
5. If an action is 'provide_tracking_update', give them a clear delivery estimate (3-5 business days) and reassure them their package is moving safely.
6. If an action is 'escalate_human', assure them a Senior Manager has taken over their ticket and will contact them shortly.
7. Keep the response concise (2-4 paragraphs).
8. Sign off warmly as:
Warm regards,
Ajara Shopper Customer Support Team"""

        try:
            import ollama
            response = ollama.chat(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Customer Subject: {subject}\nCustomer Message: {message}"}
                ],
                options={"temperature": 0.2}
            )
            return response['message']['content'].strip()
        except Exception as e:
            logger.warning(f"Ollama generation fallback triggered: {e}")
            # Human-grade template fallback
            return (
                f"Dear {customer_name or 'Customer'},\n\n"
                f"Thank you for contacting Ajara Shopper Customer Support regarding '{subject}'.\n\n"
                f"{'I have reviewed your order (#' + str(order_info['id']) + ') for ' + str(order_info['product']) + '. ' if order_info else ''}"
                f"Based on our store policy, we have logged your inquiry under our {classification.get('category', 'support').replace('_', ' ').title()} team with {classification.get('urgency', 'medium').upper()} priority. "
                f"Our automated system has initiated the required action ({action.replace('_', ' ')}). "
                f"You will receive an update within 24 to 48 hours.\n\n"
                f"Warm regards,\n"
                f"Ajara Shopper Customer Support Team"
            )

    def process_ticket(
        self,
        name: str,
        email: str,
        subject: str,
        message: str,
        order_id: str = None,
        user=None
    ) -> Dict[str, Any]:
        """
        Executes the full autonomous customer support pipeline end-to-end.
        """
        start_time = time.time()
        ticket_id = f"AJR-{uuid.uuid4().hex[:6].upper()}"

        # 1. Order DB Tool Calling
        order_info = self._lookup_order(order_id, user=user)

        # 2. Intent Classification
        classification = self._classify_intent(subject, message)

        # 3. Policy RAG Retrieval
        retrieval_query = f"{subject} {message} {classification.get('category', '')}"
        retrieved_docs = search_ecommerce_docs(retrieval_query, top_k=2)

        # 4. Deterministic Business Rules
        action = self._determine_action(classification, message, order_info)

        # 5. Grounded Human-Grade Resolution
        ai_response = self._generate_response(
            customer_name=name,
            subject=subject,
            message=message,
            classification=classification,
            action=action,
            retrieved_docs=retrieved_docs,
            order_info=order_info
        )

        latency = round(time.time() - start_time, 2)
        status = "escalated_to_human" if action == "escalate_human" else "resolved"

        return {
            "ticket_id": ticket_id,
            "name": name,
            "email": email,
            "subject": subject,
            "message": message,
            "order_id": order_id if order_id else (str(order_info["id"]) if order_info else None),
            "order_details": order_info,
            "classification": classification,
            "category": classification.get("category", "general_inquiry"),
            "urgency": classification.get("urgency", "medium"),
            "sentiment": classification.get("sentiment", "neutral"),
            "action": action,
            "status": status,
            "retrieved_policies": [d["filename"] for d in retrieved_docs],
            "ai_response": ai_response,
            "latency": latency
        }

def run_ecommerce_support(name, email, subject, message, order_id=None, user=None) -> Dict[str, Any]:
    agent = ECommerceSupportAgent()
    return agent.process_ticket(name, email, subject, message, order_id, user)
