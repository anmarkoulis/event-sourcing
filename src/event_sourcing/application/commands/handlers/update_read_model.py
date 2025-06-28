import logging

from event_sourcing.application.commands.aggregate import (
    UpdateReadModelCommand,
)
from event_sourcing.infrastructure.read_model import ReadModel

logger = logging.getLogger(__name__)


class UpdateReadModelCommandHandler:
    """Handler for updating read model with aggregate snapshots"""

    def __init__(self, read_model: ReadModel):
        self.read_model = read_model

    async def handle(self, command: UpdateReadModelCommand) -> None:
        """Handle update read model command"""
        aggregate_id = command.data["aggregate_id"]
        aggregate_type = command.data["aggregate_type"]
        snapshot = command.data["snapshot"]

        logger.info(
            f"Updating read model for: {aggregate_type} {aggregate_id}"
        )
        logger.info(f"Snapshot data: {snapshot}")

        # Update read model based on aggregate type
        if aggregate_type == "client":
            await self.read_model.save_client(snapshot)
        else:
            logger.warning(
                f"Unknown aggregate type for read model: {aggregate_type}"
            )
            return

        logger.info(
            f"Successfully updated read model for: {aggregate_type} {aggregate_id}"
        )
