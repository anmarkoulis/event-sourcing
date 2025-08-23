"""Wrapper for managing session creation in projections."""

import inspect
import logging
from typing import TYPE_CHECKING, Any, Type

from event_sourcing.infrastructure.read_model import PostgreSQLReadModel
from event_sourcing.infrastructure.unit_of_work import SQLAUnitOfWork

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover
    from .infrastructure_factory import InfrastructureFactory


class ProjectionWrapper:
    """Wrapper that manages session creation for projections."""

    def __init__(
        self, factory: "InfrastructureFactory", projection_class: Type
    ) -> None:
        """Initialize ProjectionWrapper.

        :param factory: Infrastructure factory instance.
        :param projection_class: Projection class to wrap.
        """
        self.factory = factory
        self.projection_class = projection_class

    async def _create_projection_with_session(self) -> tuple[Any, Any]:
        """Create a fresh session and projection for this operation.

        :return: Tuple of (projection, session).
        """
        session = await self.factory.session_manager.get_session()
        read_model = PostgreSQLReadModel(session)

        # Check if the projection class expects unit_of_work parameter
        sig = inspect.signature(self.projection_class.__init__)
        if "unit_of_work" in sig.parameters:
            uow = SQLAUnitOfWork(session)
            projection = self.projection_class(
                read_model=read_model,
                unit_of_work=uow,
            )
        else:
            projection = self.projection_class(read_model=read_model)

        return projection, session

    async def handle(self, event: Any) -> Any:
        """Handle the event with proper session management.

        :param event: Event to handle.
        :return: Result from projection.
        """
        projection, session = await self._create_projection_with_session()
        try:
            # The projection will handle its own transaction via Unit of Work
            return await projection.handle(event)
        finally:
            # Session is managed by the Unit of Work, just close it
            await session.close()
