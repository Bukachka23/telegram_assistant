from typing import TYPE_CHECKING

from aiogram import Router

from bot.domain.protocols import DeepResearchServiceProtocol, MonitorServiceProtocol
from bot.handlers.commands.agent import register_agent_handlers
from bot.handlers.commands.info import register_info_handlers
from bot.handlers.commands.monitor import register_monitor_handlers
from bot.handlers.commands.research import register_research_handlers
from bot.services.conversation import ConversationManager
from bot.services.metrics import MetricsService
from bot.services.telegraph import TelegraphPublishService

if TYPE_CHECKING:
    from bot.services.health import HealthService


def setup_commands(
    conversations: ConversationManager,
    monitor_service: MonitorServiceProtocol,
    deep_research: DeepResearchServiceProtocol | None = None,
    health: "HealthService | None" = None,
    telegraph: TelegraphPublishService | None = None,
    metrics: MetricsService | None = None,
) -> Router:
    """Configure command handlers with dependencies."""
    router = Router(name="commands")
    register_agent_handlers(router, conversations)
    register_info_handlers(
        router,
        conversations,
        health=health,
        telegraph=telegraph,
        metrics=metrics,
    )
    register_research_handlers(
        router,
        conversations,
        deep_research=deep_research,
        telegraph=telegraph,
    )
    register_monitor_handlers(router, monitor_service)
    return router
