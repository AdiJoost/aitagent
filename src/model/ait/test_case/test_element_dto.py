from datetime import datetime


from src.model.ait.base_dto.base_dto import BaseDTO
from src.model.ait.test_case.element_tag_dto import ElementTagDTO
from src.model.ait.test_case.helpers_dtos.ait_notification_type import AitNotificationType
from src.model.ait.test_case.helpers_dtos.state import State


class TestElementBaseDTO(BaseDTO):
    structureId: int | None = None
    elementId: int | None = None
    typeId: int | None = None
    targetRawValue: str | None = None
    targetRawValueTolerance: float | None = None
    targetTolerance: float | None = None
    factor: int | None = None
    unit: str | None = None
    timeoutInMs: int | None = None
    equipmentDesignator: str | None = None
    notificationTextEnglish: str | None = None
    notificationTextGerman: str | None = None
    notificationType: AitNotificationType | None = None
    variableName: str | None = None
    isOnReport: bool | None = None
    state: State | None = None
    targetSelection: list[str] | None = None
    resultTagDto: ElementTagDTO | None = None
    invertResult: bool | None = None
    targetVariableName: str | None = None
    toleranceVariableName: str | None = None
    timeoutVariableName: str | None = None
    comment: str | None = None

class TestElementDTO(TestElementBaseDTO):
    createDate: datetime | None = None
    changeDate: datetime | None = None
    traceNr: str | None = None
    # user_input_options <- implement later