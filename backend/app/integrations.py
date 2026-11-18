"""Explicit ports and free local adapters; never process money or send SMS."""
from typing import Protocol
from uuid import uuid4


class MobileMoneyProvider(Protocol):
    def initiate(self, *, amount_tzs: int, phone: str, provider: str) -> str: ...


class SmsProvider(Protocol):
    def send(self, *, phone: str, message: str) -> str: ...


class MockMobileMoney:
    def initiate(self, *, amount_tzs, phone, provider):
        return f'MOCK-{provider.upper()}-{uuid4().hex[:20]}'


class MockSms:
    def send(self, *, phone, message):
        return f'SMS-SIM-{uuid4().hex[:20]}'


mobile_money: MobileMoneyProvider = MockMobileMoney()
sms: SmsProvider = MockSms()
