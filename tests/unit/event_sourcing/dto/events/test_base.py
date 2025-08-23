"""Unit tests for EventDTO base class."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

from event_sourcing.dto.events.base import EventDTO
from event_sourcing.enums import EventType


class TestEventData(BaseModel):
    """Test event data class for testing EventDTO."""

    field1: str
    field2: int


class TestEventDataV1(BaseModel):
    """Test event data class with V1 suffix for version testing."""

    field1: str
    field2: int


class TestEventDataV2(BaseModel):
    """Test event data class with V2 suffix for version testing."""

    field1: str
    field2: int
    field3: bool


class TestEventDTO(EventDTO[TestEventData]):
    """Test EventDTO subclass for testing."""


class TestEventDTOV1(EventDTO[TestEventDataV1]):
    """Test EventDTO subclass with V1 suffix for version testing."""


class TestEventDTOV2(EventDTO[TestEventDataV2]):
    """Test EventDTO subclass with V2 suffix for version testing."""


class TestEventDTONoVersion(EventDTO[TestEventData]):
    """Test EventDTO subclass without version suffix."""


class TestEventDTOClass:
    """Test cases for EventDTO base class."""

    @pytest.fixture
    def aggregate_id(self) -> uuid.UUID:
        """Provide a test aggregate ID."""
        return uuid.uuid4()

    @pytest.fixture
    def timestamp(self) -> datetime:
        """Provide a fixed timestamp for testing."""
        return datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    @pytest.fixture
    def test_data(self) -> TestEventData:
        """Provide test event data."""
        return TestEventData(field1="test_value", field2=42)

    def test_init_with_required_fields(
        self,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
        test_data: TestEventData,
    ) -> None:
        """Test EventDTO initialization with required fields."""
        event = EventDTO(
            aggregate_id=aggregate_id,
            event_type=EventType.USER_CREATED,
            timestamp=timestamp,
            version="1",
            revision=1,
            data=test_data,
        )

        assert event.aggregate_id == aggregate_id
        assert event.event_type == EventType.USER_CREATED
        assert event.timestamp == timestamp
        assert event.version == "1"
        assert event.revision == 1
        assert event.data == test_data
        assert isinstance(event.id, uuid.UUID)

    def test_init_with_default_id(
        self,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
        test_data: TestEventData,
    ) -> None:
        """Test EventDTO initialization with default ID generation."""
        event1 = EventDTO(
            aggregate_id=aggregate_id,
            event_type=EventType.USER_CREATED,
            timestamp=timestamp,
            version="1",
            revision=1,
            data=test_data,
        )

        event2 = EventDTO(
            aggregate_id=aggregate_id,
            event_type=EventType.USER_CREATED,
            timestamp=timestamp,
            version="1",
            revision=1,
            data=test_data,
        )

        # IDs should be different (auto-generated)
        assert event1.id != event2.id
        assert isinstance(event1.id, uuid.UUID)
        assert isinstance(event2.id, uuid.UUID)

    def test_init_with_custom_id(
        self,
        aggregate_id: uuid.UUID,
        timestamp: datetime,
        test_data: TestEventData,
    ) -> None:
        """Test EventDTO initialization with custom ID."""
        custom_id = uuid.uuid4()
        event = EventDTO(
            id=custom_id,
            aggregate_id=aggregate_id,
            event_type=EventType.USER_CREATED,
            timestamp=timestamp,
            version="1",
            revision=1,
            data=test_data,
        )

        assert event.id == custom_id

    def test_get_version_v1_suffix(self) -> None:
        """Test get_version method for class with V1 suffix."""
        version = TestEventDTOV1.get_version()
        assert version == "1"

    def test_get_version_v2_suffix(self) -> None:
        """Test get_version method for class with V2 suffix."""
        version = TestEventDTOV2.get_version()
        assert version == "2"  # Now properly handles V2

    def test_get_version_no_suffix(self) -> None:
        """Test get_version method for class without version suffix."""
        version = TestEventDTONoVersion.get_version()
        assert version == "1"  # Default version

    def test_get_version_base_class(self) -> None:
        """Test get_version method for base EventDTO class."""
        version = EventDTO.get_version()
        assert version == "1"  # Default version

    def test_get_version_dynamic_class_creation(self) -> None:
        """Test get_version method for dynamically created classes."""
        # Create a class dynamically with V3 suffix
        TestEventDTOV3 = type(
            "TestEventDTOV3",
            (EventDTO,),
            {"__annotations__": {"data": TestEventData}},
        )

        # Cast to EventDTO to help mypy understand the type
        from typing import cast

        event_dto_class = cast(type[EventDTO], TestEventDTOV3)
        version = event_dto_class.get_version()
        assert version == "3"  # Now properly handles V3

    def test_get_version_complex_class_name(self) -> None:
        """Test get_version method for complex class names."""
        # Create a class with complex name ending in V1
        ComplexNameV1 = type(
            "ComplexNameV1",
            (EventDTO,),
            {"__annotations__": {"data": TestEventData}},
        )

        # Cast to EventDTO to help mypy understand the type
        from typing import cast

        event_dto_class = cast(type[EventDTO], ComplexNameV1)
        version = event_dto_class.get_version()
        assert version == "1"

    def test_get_version_no_version_pattern(self) -> None:
        """Test get_version method for class without version pattern."""
        # Create a class without version pattern
        NoVersionClass = type(
            "NoVersionClass",
            (EventDTO,),
            {"__annotations__": {"data": TestEventData}},
        )

        # Cast to EventDTO to help mypy understand the type
        from typing import cast

        event_dto_class = cast(type[EventDTO], NoVersionClass)
        version = event_dto_class.get_version()
        assert version == "1"  # Default version

    def test_get_version_lowercase_v(self) -> None:
        """Test get_version method for lowercase v suffix."""
        # Create a class with lowercase v suffix
        LowercaseV2 = type(
            "LowercaseV2",
            (EventDTO,),
            {"__annotations__": {"data": TestEventData}},
        )

        # Cast to EventDTO to help mypy understand the type
        from typing import cast

        event_dto_class = cast(type[EventDTO], LowercaseV2)
        version = event_dto_class.get_version()
        assert version == "2"

    def test_get_version_mixed_case(self) -> None:
        """Test get_version method for mixed case version suffixes."""
        # Test various mixed case patterns
        test_cases = [
            ("UserCreatedV1", "1"),
            ("UserCreatedV2", "2"),
            ("UserCreatedv1", "1"),
            ("UserCreatedv2", "2"),
            ("UserCreatedV10", "10"),
            ("UserCreatedv99", "99"),
            ("ComplexNameV42", "42"),
            ("SimpleName", "1"),  # Default
        ]

        from typing import cast

        for class_name, expected_version in test_cases:
            TestClass = type(
                class_name,
                (EventDTO,),
                {"__annotations__": {"data": TestEventData}},
            )
            # Cast to EventDTO to help mypy understand the type
            event_dto_class = cast(type[EventDTO], TestClass)
            version = event_dto_class.get_version()
            assert version == expected_version, (
                f"Expected {expected_version} for {class_name}, got {version}"
            )

    def test_type_safety_with_generic(self) -> None:
        """Test that EventDTO maintains type safety with generics."""
        event = EventDTO[TestEventData](
            aggregate_id=uuid.uuid4(),
            event_type=EventType.USER_CREATED,
            timestamp=datetime.now(timezone.utc),
            version="1",
            revision=1,
            data=TestEventData(field1="test", field2=42),
        )

        # Type checker should know that data is TestEventData
        assert event.data.field1 == "test"
        assert event.data.field2 == 42

    def test_revision_validation(self) -> None:
        """Test that revision must be >= 1."""
        with pytest.raises(
            ValueError, match="Input should be greater than or equal to 1"
        ):
            EventDTO(
                aggregate_id=uuid.uuid4(),
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=0,  # Invalid: must be >= 1
                data=TestEventData(field1="test", field2=42),
            )

    def test_version_validation(self) -> None:
        """Test that version must have minimum length of 1."""
        with pytest.raises(
            ValueError, match="String should have at least 1 character"
        ):
            EventDTO(
                aggregate_id=uuid.uuid4(),
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="",  # Invalid: empty string
                revision=1,
                data=TestEventData(field1="test", field2=42),
            )

    def test_required_fields_validation(self) -> None:
        """Test that required fields cannot be None."""
        # Now the data field properly validates that None is not allowed
        with pytest.raises(ValueError, match="Event data cannot be None"):
            EventDTO(
                aggregate_id=uuid.uuid4(),
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=None,  # This should now raise an error
            )

    def test_event_type_enum_validation(self) -> None:
        """Test that event_type must be a valid EventType enum value."""
        with pytest.raises(ValueError):
            EventDTO(
                aggregate_id=uuid.uuid4(),
                event_type="INVALID_EVENT_TYPE",  # Invalid: must be EventType enum
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=TestEventData(field1="test", field2=42),
            )

    def test_aggregate_id_validation(self) -> None:
        """Test that aggregate_id must be a valid UUID."""
        with pytest.raises(ValueError):
            EventDTO(
                aggregate_id="not-a-uuid",  # Invalid: must be UUID
                event_type=EventType.USER_CREATED,
                timestamp=datetime.now(timezone.utc),
                version="1",
                revision=1,
                data=TestEventData(field1="test", field2=42),
            )

    def test_timestamp_validation(self) -> None:
        """Test that timestamp must be a valid datetime."""
        with pytest.raises(ValueError):
            EventDTO(
                aggregate_id=uuid.uuid4(),
                event_type=EventType.USER_CREATED,
                timestamp="not-a-datetime",  # Invalid: must be datetime
                version="1",
                revision=1,
                data=TestEventData(field1="test", field2=42),
            )
