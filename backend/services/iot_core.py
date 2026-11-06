"""
Virtual AWS IoT Core MQTT Broker for Smart Visitor Counter.
Handles topic subscriptions, QoS 1 acknowledgements, and Topic Rules.
"""

from datetime import datetime
from typing import Dict, Any, List

class VirtualIoTCore:
    def __init__(self):
        self.topic = "campus/library/turnstile/visitor_in"
        self.qos = 1
        self.connected_devices = ["ESP32-VISITOR-NODE-01"]
        self.total_messages_received = 0
        self.rules = [
            {
                "rule_name": "RouteVisitorPressToLambda",
                "sql": "SELECT * FROM 'campus/library/turnstile/visitor_in'",
                "action": "arn:aws:lambda:us-east-1:218062175263:function:ProcessVisitorCounter",
                "enabled": True
            }
        ]
        self.recent_mqtt_packets: List[Dict[str, Any]] = []

    def publish_message(self, payload: dict) -> dict:
        self.total_messages_received += 1
        now = datetime.utcnow().isoformat() + "Z"
        packet = {
            "packet_id": self.total_messages_received,
            "topic": self.topic,
            "qos": self.qos,
            "timestamp": now,
            "payload": payload,
            "status": "ACCEPTED_AND_ROUTED"
        }
        self.recent_mqtt_packets.insert(0, packet)
        if len(self.recent_mqtt_packets) > 30:
            self.recent_mqtt_packets.pop()
        return packet

    def get_metrics(self) -> dict:
        return {
            "broker_status": "CONNECTED",
            "topic": self.topic,
            "qos": self.qos,
            "connected_devices_count": len(self.connected_devices),
            "connected_devices": self.connected_devices,
            "total_messages": self.total_messages_received,
            "active_rules": len(self.rules),
            "recent_packets": self.recent_mqtt_packets[:5]
        }

iot_core = VirtualIoTCore()
